---
type: "Runbook"
title: "310P fp32 matmul 逐位复现：裸 Mmad"
description: "310P 的 torch fp32 matmul 内部是 fp16 输入 + fp32 累加；纯 fp32/拼接实现会在 fp32 末态门上差 1 ulp。要逐位复现，用裸 Mmad 按同一 Kpad/CO1 布局重算。"
tags: [task.debugging, topic.precision, topic.programming_model.execution_unit.cube]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/basic_api/kernel_struct_mm.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/impl/basic_api/dav_m200/kernel_operator_mm_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/adv_api/matmul/matmul_intf.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/a6a99bcf65cdf43202e0e270ea1f9cdc79cf1c23/include/adv_api/matmul/matmul.h
    role: header
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-22T04:01:25Z'
platforms: ["310p"]
---

# 310P fp32 matmul 逐位复现：裸 Mmad

## 现象

在一个逐时间步顺序递推的反向算子里，`dq/dk` 等逐元素/行归约输出都能过，唯独 `dh0`（fp32 末态，门 `MERE < 2^-13`）在部分 case 上差约 1e-4。把实现改成“更准”的纯 fp32 向量路径没有用——它和 CPU fp64 只差 1e-7，但和 device 上的参考差 1e-4；参考的 matmul 本身不是精确 fp32。

用同一份参考做逐位对照：`n=1` 的 matvec 与 `n=16` 的 matmul 结果**逐位相同**——这只能说明两者走同一条路径，**不能单独区分纯 fp32 与 fp16-internal**（不同 fp32 归约顺序也可能产生相近量级的差异），只能当排查线索。真正区分操作数量化的是**两操作数探针**：A、B 都取非平凡值（避免 1/0），比较 device 结果与 `Q16(A)@Q16(B)`（fp32 累加）模型、纯 fp32 模型。本轨迹的直接对照（K/V=64/48、64/64、24/61、128/112 四组）：device 参考与 `Q16(S_t)@Q16(do)` 逐位相同（`gold-rnd=0.000e+00`、`bitexact=True`），与纯 fp32 因式分解模型差 6.984e-04–2.272e-03；而纯 fp32 的向量实现无论怎么换累加次序（seq/tree/slice8/16/32/lane8/reverse 七种），都与 device 差 1–4 ulp。结论：**参考的 fp32 matmul 是 fp16 输入 + fp32 累加**，要过 fp32 末态门，只能用同一硬件单元复现它的操作数舍入与累加次序。

## 适用场景

- **工程形态**：AscendC kernel 直调；310P 上移植/生成“参考实现用 torch matmul、输出含 fp32 末态”的算子（顺序递推、状态输出、长链 GEMM）。
- **API 路径**：`Mmad` + `MmadParams` + `LoadData2dParams`/`LoadData` + `DataCopy(L0C→UB, BLOCK_MODE_MATRIX)`；`Cast(CAST_NONE)` 做 fp32→fp16（RNE）。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0。
- **适用粒度**：`platform_wide` —— 310P 上任何“参考 matmul 是 fp16-internal、输出按 fp32 紧门比较”的场景。
- **路线优先级**：`recommended_fastpath` —— 先判“参考 matmul 是否 fp16-internal”；是则直接上裸 Mmad，不要在向量路径里试累加次序。若参考是真 fp32（如 CPU fp64/fp32 golden），本路线不适用。
- **明确不适用 / 未验证场景**：参考是 CPU 真 fp32、或输出门较松（纯 fp32 已能过）的场景；`Kpad > 128` 的更大状态；非 fp32 输出门；其它代际未验证。

## 根因

310P 的 `torch.matmul`（fp32 输入）在 device 上走 cube，内部把两个操作数先按 **fp16 RNE** 舍入，再做 **fp32 累加**：

```
s = Σ_taps Q16(x) · Q16(w)        # fp32 累加（cube L0C）
out = s                            # 直接写 fp32（本类参考不再舍入）
```

纯 fp32 的向量实现做的是 `Σ x·w`，每个乘积和累加都比参考多保留约 13 位有效位；单步差 ~1 fp32 ulp，但顺序递推会把差异按步数累积，并在 fp16 舍入边界放大，末态 `dh0` 就过不了 `MERE < 2^-13`。软件换累加次序无法复现 cube 的 L0C 累加顺序；唯一可行路径是**用同一硬件单元、同样的 fp16 操作数、同样的 K 分块**重算。

这也是为什么“实现比参考更准”反而失败：精度门绑定的是 device golden，不是数学真值。

## 判别方法

1. **直接判操作数量化（首选）**：取两个都非平凡的操作数 A、B（不要用 1/0），在 device 上算 `gold = A @ B`；CPU 侧构造 `rnd = Q16(A) @ Q16(B)`（fp32 累加）与 `fact = 纯 fp32 A @ B`。若 `gold` 与 `rnd` 逐位相同、与 `fact` 差 ~1e-3，则参考是 fp16-internal；若 `gold` 与 `fact` 一致，则不是。`n=1`（matvec）与 `n=16`（matmul）逐位相同只能作为“走同一路径”的辅助线索，不能单独作为判据。
2. **再判输出门**：把纯 fp32 实现与 CPU fp64 比（应 ~1e-7），再与 device golden 比（若差 1e-4 量级且集中在 fp32 末态输出），即为“参考 fp16-internal”的指纹。
3. **最后判是否值得上 cube**：若 fp32 末态门是 `MERE < 2^-13` 这类紧门，向量路径的累加次序试验可以直接跳过；直接做 `C[64,Vpad] = A[64,Kpad] @ B[Kpad,Vpad]` 的裸 Mmad 探针。

## 解决配方

### Before：向量折半列归约（数学正确，但累加次序不可复现）

```cpp
                if (!useCube_) {
                    // dv_base chunk = round16(dS) . k  (column fold inside the chunk)
                    Cast(tmp[oc], hChunk, RoundMode::CAST_NONE, m, kpad,
                         UnaryRepeatParams(1, 1, vblocks, static_cast<uint8_t>((m + 15) / 16)));
                    Mul(tmp[oc], tmp[oc], stk, m, kpad,
                        BinaryRepeatParams(1, 1, 0, vblocks, vblocks, 1));
                    for (int32_t j = 1; j <= logK_; ++j) {
                        const int32_t mm = kpad >> j;
                        Add(tmp[oc], tmp[oc], tmp[oc + mm * vpad], m, mm,
                            BinaryRepeatParams(1, 1, 1, vblocks, vblocks, vblocks));
                    }
                    if (c == 0) {
                        Adds(dvb, tmp, 0.0f, vpad);
                    } else {
                        Add(dvb[oc], dvb[oc], tmp[oc], m);
                    }
                }
```

### After：裸 Mmad 逐位复现

```cpp
    // dvn via bare Mmad: C[64,Vpad] = k_row @ round16(dS); row 0 is dvn.
    // Bit-exact with the device's own matmul (probe P7 / scripts/probe_mm_bitexact.py).
    __aicore__ inline void CubeDvn(const LocalTensor<float> &ds, const LocalTensor<float> &kR,
                                   const LocalTensor<float> &dvb)
    {
        LocalTensor<half> hTile = hBuf_.Get<half>();
        LocalTensor<half> aUb = aCubeBuf_.Get<half>();
        LocalTensor<half> l1A = l1ACube_.Get<half>();
        LocalTensor<half> l1B = l1BCube_.Get<half>();
        LocalTensor<half> l0A = l0ACube_.Get<half>();
        LocalTensor<half> l0B = l0BCube_.Get<half>();
        LocalTensor<float> co = coCube_.Get<float>();
        const uint16_t n1 = static_cast<uint16_t>(Vpad_ / 16);
        const uint16_t k1 = static_cast<uint16_t>(Kpad_ / 16);
        Cast(hTile, ds, RoundMode::CAST_NONE, Kpad_ * Vpad_);
        Cast(aUb, kR, RoundMode::CAST_NONE, Kpad_);              // row 0 = k (rows >= 1 stay 0)
        Evt<HardEvent::V_MTE3>();
        Evt<HardEvent::MTE1_MTE3>();
        for (uint32_t j = 0; j < k1; ++j) {
            DataCopy(l1A[j * 64 * 16], aUb[j * 16],
                     {64, 1, static_cast<uint16_t>(k1 - 1), 0});
        }
        for (uint32_t j = 0; j < n1; ++j) {
            DataCopy(l1B[j * Kpad_ * 16], hTile[j * 16], {static_cast<uint16_t>(Kpad_), 1,
                     static_cast<uint16_t>(n1 - 1), 0});
        }
        Evt<HardEvent::MTE3_MTE1>();
        Evt<HardEvent::MTE3_V>();   // later vector ops reuse the UB staging tile
        Evt<HardEvent::M_MTE1>();
        LoadData2dParams la(0, k1, 4, 0, 0, false, 0);   // A slice stride = 64*16 halfs = 4 fractals
        for (uint32_t i = 0; i < 4; ++i) {
            LoadData(l0A[i * k1 * 256], l1A[i * 256], la);
        }
        LoadData2dParams lb(0, n1, static_cast<uint8_t>(k1), 0, 0, true, 0);  // B slice stride = Kpad*16 halfs
        for (uint32_t i = 0; i < k1; ++i) {
            LoadData(l0B[i * n1 * 256], l1B[i * 256], lb);
        }
        Evt<HardEvent::MTE1_M>();
        MmadParams mp(64, static_cast<uint16_t>(Vpad_), static_cast<uint16_t>(Kpad_), 0, false, true);
        Mmad(co, l0A, l0B, mp);
        Evt<HardEvent::M_V>();
        DataCopyEnhancedParams enh;
        enh.blockMode = BlockMode::BLOCK_MODE_MATRIX;
        LocalTensor<float> cTmp = tmpBuf_.Get<float>();
        DataCopy(cTmp, co, {n1, 4, 0, 0}, enh);
        PipeBarrier<PIPE_V>();
        for (uint32_t j = 0; j < n1; ++j) {
            Muls(dvb[j * 16], cTmp[j * 64 * 16], 1.0f, static_cast<uint64_t>(16), 1, {1, 1, 1, 2});
        }
        PipeBarrier<PIPE_ALL>();
    }
```

调用点：

```cpp
            if (useCube_) {
                CubeDvn(ds, kR, dvb);
            }
```

### 四个必须正确的细节

1. **形状**：`C[64,Vpad] = A[64,Kpad] @ B[Kpad,Vpad]`，A 第 0 行放 `k`、其余行置零；C 的第 0 行即 `Σ_k k[k]·dS[k,:]`（= `dS^T k`）。`m=64` 固定，`Kpad` 补到 64/128；零行/零列不影响 fp32 和。
2. **`LoadData2dParams` 的 `srcStride`（A/B 两侧不同）**：A 侧 `LoadData2dParams la(0, k1, 4, ...)` 的 `srcStride` 固定 **4 个分形**（A 的 L1 块 = 64×16 half = 512B，即 PM/16=4）；B 侧 `LoadData2dParams lb(0, n1, k1, ...)` 的 `srcStride` 是 **Kpad/16**（B 的 L1 行块高 = Kpad）。两者不能互换；`Kpad=64` 时 A 的 4 与 k1 相等，会掩盖 A 侧误写 `k1` 的 bug。
3. **CO1 读出映射**：`DataCopy(cTmp, co, {n1, 4, 0, 0}, BLOCK_MODE_MATRIX)` 得到的是 `C[mf*16+r, j*16+c] = raw[j][mf][r][c]`；再用 `Muls(dvb[j*16], cTmp[j*64*16], 1.0f, 16, 1, {1,1,1,2})` 抽出第 0 行。
4. **同步链**：UB→L1 前 `V_MTE3` + `MTE1_MTE3`；LoadData 前 `M_MTE1`；Mmad→读出 `M_V`；少一条整片数据全错。末尾 `PipeBarrier<PIPE_ALL>` 给后续向量复用 UB 留边沿。

## 设计决策

- **为什么用裸 `Mmad` 而不是高阶 `MatmulImpl<>`**：不是因为它不可用——`matmul_intf.h:29` 的 `#if 2201/3510/9201` 只门控 KFC include，`matmul.h:51-70` 对所有 arch 定义 `MatmulImpl`；7 号 `conv_standard2d_v4_gemm.cpp:36/56` 就在 2002 上用 `matmul::Matmul` 且 56/56。选裸 `Mmad` 是为了直接控制 K 分块、操作数舍入与同步边沿（本卡需要逐位复现）。
- **为什么 `m=64` 固定**：`Mmad` 的 M 维 16 分形；用 64 行可以让 A 面板一次装下 4 个 m 分形，C 的读出也按 `nf` 分形对齐；实际只消费第 0 行。
- **为什么 Kpad 取 64/128**：`Kpad` 必须 16 对齐；64 是单块 `k1=4` 的甜点，128 覆盖 K>64 的 case（UB 238 KB < 248 KB，实测可行）。
- **为什么保留向量回退**：`KDA_CUBE_ENABLE` 是 A/B 开关；cube 路径只在需要 fp32 末态逐位复现时启用，向量路径仍用于其它输出与调试。
- **当前方案路线档位**：`recommended_fastpath`（当参考是 fp16-internal 时）。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0；kernel 直调。
- 相关文件：`op_kernel/kda_bwd.cpp`（`CubeDvn` 与向量回退）；探针 `scripts/probe_mm_bitexact.py`。
- 实现证据：`asc-devkit/include/basic_api/kernel_struct_mm.h:43-66`（`LoadData2DParams`）、`:425-470`（`MmadParams`）；`impl/basic_api/dav_m200/kernel_operator_mm_impl.h:411`（`MmadCal`）。

## 完整代码

`CubeDvn` 已在上文逐字内联；向量回退的 `dvb` 折半列归约也逐字内联。两段代码对应开发会话中 `op_kernel/kda_bwd.cpp` 的修复后状态：CubeDvn 的 `k1` 已按 `Kpad_/16` 泛化（覆盖 Kpad=64/128），向量回退的列偏移在同轮修复中改为 `tmp[oc]`。`useCube_` 的判定在开发过程中曾短暂放宽到 `Kpad_<=128`、随后回退，最终以 `KDA_CUBE_ENABLE` 作为开关（不再按 Kpad 限制）。

## 性能影响

同一算子内部相对代价（310P，标准 `msprof quick` kernel 级 `Task_Duration`）：

- cube 路径的 per-step 成本高于向量折半（多一次 Kpad×Vpad 的 L1/L0 往返与读出），但它把 `dh0` 从“部分 case 不可过”变为逐位一致；
- 相对参考实现仍为正加速（同轮 40 例全部 ≥1×；不在此列绝对加速比）；
- 参照路线：向量折半列归约；来源平台：310P。

## 预防

- 先判参考 matmul 是否 fp16-internal：用两个非平凡操作数的乘积探针（`gold` vs `Q16(A)@Q16(B)` vs 纯 fp32）；不要只靠 `n=1` 与 `n=16` 逐位相同，后者只是路径线索。
- `Kpad` 必须 16 对齐并补到 64/128；补零行/列不会改变 fp32 和。
- `LoadData2dParams.srcStride` 分 A/B 两侧：A 侧固定 4 个分形，B 侧是 `Kpad/16`；不能统一写成 `k1`。`Kpad=64` 时 A 侧两者相等，必须用 `Kpad=128` 的 case 才能暴露 A 侧误写。
- CO1 读出按 `BLOCK_MODE_MATRIX` 的 `[j][mf][r][c]` 映射，不要按行主序读。
- 四条同步边沿缺一不可；用 `Evt<HardEvent::...>` 显式给边沿，不要靠 `PipeBarrier` 猜。

## 验证信号

来源：KdaBwd 310P 战役的同一条开发轨迹（单条轨迹、单次上板；证据等级 `tool_observed`/`artifact_verified`）。实现机制由 asc-devkit 固定提交 `a6a99bcf` 的头文件/impl 独立核对。

- 裸 Mmad 探针与 device 上 `dS.transpose(-2,-1) @ k` 在 **Kpad=64/128 且 K≤80** 的已验证形状上逐位相同（`maxdiff=0`）；K=128/V=100 的裸探针仍 `bit-exact=False`（maxdiff=4.198e+01），修 B 侧 srcStride 后只证明 K=80/Kpad=128 逐位。K=128 的端到端 case 由主内核精度验证，不是裸探针全形状逐位。（来源平台：310P；证据等级：tool_observed）
- 接入主内核后 `dv/dbeta` 逐位一致、`dh0` 逐位一致；KdaBwd 精度 50/50（最差 matched 0.9986 / MERE 1.5e-6）。（来源平台：310P；证据等级：artifact_verified）
- 纯向量 fp32 路径在 `dh0` 上超 `MERE < 2^-13`；七种累加次序（seq/tree/slice8/16/32/lane8/reverse）均与 device 差 1–4 ulp。（来源平台：310P；证据等级：tool_observed）
- 两操作数直接探针（K/V=64/48、64/64、24/61、128/112）：device `g = S_t @ do` 与 `r = Q16(S_t) @ Q16(do)` 四组全部 `gold-rnd=0.000e+00`、`bitexact(g,r)=True`；与纯 fp32 因式分解 `f` 的差为 6.984e-04–2.272e-03（`gold-fact`）。（来源平台：310P；证据等级：tool_observed）

## 失效边界

- **参考是真 fp32**：若 golden 是 CPU fp64/fp32 真值，本卡的 fp16-internal 复现反而会引入 ~1e-3 误差；不要用。
- **探针退化**：任一操作数为 1/0、或只有单操作数脉冲时，操作数量化与“只量化输出”可能给出相同结果；必须用两个非平凡操作数的乘积探针。
- **输出门较松**：若纯 fp32 已能过门，cube 路径只增加成本，不必上。
- **Kpad > 128**：未验证；UB 预算（Kpad*Vpad*4 × 3 块 + 向量区）可能超 248KB。
- **`nch_ > 1` 的列分块**：本卡的 `CubeDvn` 在 `Vpad>64` 时按 `n1` 分形读出；列分块的累加偏移是另一个已修复的 bug（`tmp` vs `tmp[oc]`），不要与本卡混用。
- **跨代际**：只验证 310P；其它代际的 fp32 matmul 语义不同（未验证，推断不可迁移）。

## 坏实践

- 在向量路径里反复换累加次序，试图“凑”出 device 的 fp32 末态；七种次序都差 1–4 ulp，方向本身就错。
- 因为误读 `matmul_intf.h:29` 的 `#if` 就断言“高阶 Matmul 在 2002 不可用”；该 `#if` 只门控 KFC，通用 `MatmulImpl` 在 `matmul.h` 里对所有 arch 可用。
- 把 `LoadData2dParams.srcStride` 写成 `k1`；`Kpad=64` 时能过，`Kpad=128` 时整片错。
- 只给 `Mmad` 前同步、不给读出前 `M_V`，或漏掉 UB→L1 的 `V_MTE3`+`MTE1_MTE3`；症状是整片数据全错（maxdiff 3e4 级）。

## 误诊

- 第一轮把 `dh0` 的 1e-4 当成“实现精度不够”，试了 fp64 中间量、Kahan 求和、不同 tile 顺序；实际是参考本身是 fp16-internal，纯 fp32 越准越不匹配。
- 第二轮把 `n=1` 的 matvec 当成特殊 GEMV 路径，想单独优化；逐位对照显示 `n=1` 与 `n=16` 同路径（线索），之后用两操作数探针才确认 fp16-internal。
- 也曾把 `matmul_intf.h` 的 KFC `#if` 误读成“`MatmulImpl` 被 arch 门控”；后来在 7 号 v4 gemm 里看到 `matmul::Matmul` 在 2002 上 56/56，才纠正。
