---
type: "Runbook"
title: "310P conv eager 参考的 fp16 语义四档"
description: "310P conv 族 eager 参考把操作数量化到 fp16 RNE；Conv2D/depthwise 输出 fp32，Conv3D/ConvTranspose2d 额外做 fp16(fp16(Σ)+fp16(bias))。两个非平凡乘数的乘积探针 5 分钟识别；单操作数探针只作预筛。"
tags: [task.debugging, topic.precision, topic.compute.neighborhood.convolution]
status: stable
sources: []
created_at: '2026-11-05T07:33:56Z'
updated_at: '2026-11-11T09:46:56Z'
platforms: ["310p"]
---

# 310P conv eager 参考的 fp16 语义四档

## 现象

310P 上四个 conv 算子在切换到混合容差精度门后同时失败：候选与 eager 对比 `matched_ratio 0.80–0.99`、`max_abs 1e-3–4e-3`，全部 fp32 输出。但把候选与 CPU fp64 golden 一比就分域：**候选 vs fp64 ≈ 1e-7（实现是精确的），eager vs fp64 ≈ 1e-3（参考是 fp16 化的）**。失败方向是“实现太准”，不是“实现不准”。

## 适用场景

- **工程形态**：310P 上的 AscendC conv/depthwise/conv-transpose 算子，参考实现是 `torch_npu` eager（`nn.Conv2d`/`nn.ConvDepthwise2d`/`nn.Conv3d`/`nn.ConvTranspose2d`）。
- **API 路径**：torch_npu eager conv（参考侧）；AscendC `Cast`/`Adds`/`Axpy`/`Mmad`（候选侧）。
- **验证过的平台与 CANN 版本**：Ascend310P3（DAV_2002 / dav-m200）+ CANN 9.0.0 + torch_npu 2.9。
- **适用粒度**：`operator_family` —— 310P conv 族；不限于某一个算子。
- **路线优先级**：`recommended_fastpath` —— 先做单值探针识别参考的量化档位，再按档位对齐；不要在纯 fp32 实现上继续调 tiling。
- **明确不适用 / 未验证场景**：CPU fp32/fp64 golden（真值不是 fp16-internal）；非 conv 族算子；其它代际的 eager 语义未验证。

## 根因

310P 的 torch_npu eager conv 在 device 上把操作数按 **fp16 RNE** 量化，再按算子族走不同的累加/输出舍入：

| 参考算子 | 操作数 | 累加 | 输出 |
|---|---|---|---|
| `Conv2D`（dense cube，含 depthwise 1×1） | fp16 RNE | fp32 | **fp32（不额外舍入）** |
| `depthwise conv2d` | fp16 RNE | fp32 | **fp32（不舍入）** |
| `Conv3D` | fp16 RNE | fp32 | **fp16(fp16(Σ)+fp16(bias)) 再写 fp32** |
| `ConvTranspose2d` | fp16 RNE | fp32 | **fp16(fp16(Σ)+fp16(bias)) 再写 fp32** |

判别“输出是否 fp16 舍入”的一行探针：`torch.equal(e.half().float(), e) → True` 即参考内部输出是 fp16 张量（Conv3D/ConvTranspose2d 已逐例验证为 True；Conv2D/depthwise 不加输出 H2 即可过门，未逐例打印该探针）。

H2 模型（Conv3D/ConvTranspose2d 的精确复现）：

```
s   = Σ_taps Q16(x)·Q16(w)        # fp32 累加（cube L0C）
out = Q16( Q16(s) + Q16(bias) )   # 再转回 fp32 存储
```

注意中间那次 `Q16(s)` 不可省：只做 `Q16(s+bias)`（H1 模型）在 Conv3D 上只有 0.989–0.995 matched；H2 是 1.000。bias 也必须先 Q16 再相加。

## 判别方法

**乘积探针（首选，5 分钟出结论）**：构造 `nn.Conv2d/Conv3d/ConvTranspose2d(1,1,k,bias=False)`（若用默认构造，先显式 `bias.zero_()`；默认 bias 会叠加到输出），权重只留一个 tap = `w_val`、输入单点脉冲 = `v_val`，**两个值都取非平凡值**（不要用 1/0；例如 `w_val=0.123456789`、`v_val=0.30000001`），输出就是两个操作数量化后的乘积。与以下模型对表：

- `Q16(v)·Q16(w)`：两个操作数都 fp16 RNE；
- `Q16(v·w)`：只量化输出（操作数不量化）；
- `v·Q16(w)` 或 `Q16(v)·w`：只量化一个操作数；
- 同形的 RTZ/bf16/m10/m13 版本。

只有两个乘数都非平凡时，上述模型才给出可区分的预测；单操作数（另一个乘数为 1）探针无法区分“操作数量化”与“只量化输出”，只能作快速预筛（排除 RTZ/bf16/13bit），不能单独证明两个操作数都被量化。

**单操作数预探针（辅助）**：权重只留一个 tap = `w_val`、输入全 1（或反之：输入单点脉冲 = `v_val`、权重 = 1），输出是**一个操作数**的量化结果，直接对表。2026-10-31 实测 310P：权重与输入分别落在 fp16 RNE（0.123456789→0.12347412、0.30000001→0.30004883；RTZ/bf16/13bit 对不上）。这些是单操作数预探针结果，**不是两操作数判据**；本卡的两操作数量化确认由 H2 模型 9/9 matched≈1.00000 承担（8 例 1.00000、case 0 为 0.99997；只有两个操作数都 Q16 才能逐位命中）。

**输出档位探针**：`torch.equal(e.half().float(), e)`；再与 H1/H2 两个模型逐 case 对照，取 matched=1.0 的那个。

## 解决配方

### 候选侧：fp32 lane 的 fp16 往返

**Before**：窗口和权重按 fp32 直接参与 Axpy（taps 直接读 `winW_`）：

```cpp
                TC taps[MAX_TAPS];
                for (int64_t t = 0; t < KK_; ++t) {
                    taps[t] = static_cast<TC>(
                        winW_[cl * WKA_ + hW].GetValue(static_cast<uint32_t>(t)));
                }
```

**After**：在 A 相屏障后对输入窗/权重窗做 fp32→fp16(RNE)→fp32 往返，taps 改从 half 缓冲读取：

```cpp
    static constexpr bool QUANT_F16 = std::is_same_v<T, float> && std::is_same_v<TC, float>;

            if constexpr (QUANT_F16) {
                // eager-parity：输入窗 fp32→fp16(RNE)→fp32（V 管道内序）；权重窗整带
                // 一次量化；V→S 交叉由末尾 PIPE_ALL 保证（taps 标量读）。
                AscendC::Cast(qh_, winTab_, AscendC::RoundMode::CAST_NONE,
                              static_cast<uint32_t>(CB_ * ROWS_ * WINLEN_));
                AscendC::Cast(winTab_, qh_, AscendC::RoundMode::CAST_NONE,
                              static_cast<uint32_t>(CB_ * ROWS_ * WINLEN_));
                AscendC::Cast(qhW_, winW_, AscendC::RoundMode::CAST_NONE,
                              static_cast<uint32_t>(cCnt * WKA_));
                AscendC::PipeBarrier<PIPE_ALL>();  // V -> S（taps 标量读）
            }
```

`CAST_NONE` 即 RNE，等价 torch `.half()`；fp32→fp16→fp32 往返把输入窗/权重窗量化到参考的操作数域。权重标量从 half 缓冲 `GetValue` 后 `static_cast<float>` 精确扩展；V→S 之间必须 `PipeBarrier<PIPE_ALL>`。

### Conv3D/ConvTranspose2d：H2 epilogue

```cpp
                        // bias 仍逐行 fp16 Adds（系数不同）。逐元素语义与逐行版完全一致。
                        Cast(tileH, tile, RoundMode::CAST_NONE, nM);
                        // ...
                                Adds(tileH[coIn * M], tileH[coIn * M], bvH,
                                     static_cast<int32_t>(M));
                        // ...
                        Cast(tile, tileH, RoundMode::CAST_NONE, nM);
```

ConvTranspose2d 的同一形态：

```cpp
                    Cast(rowHalf_, planeT, RoundMode::CAST_NONE, nAll);
                    // ...
                        const half bcoH = biasHalf_.GetValue(coG);
                        Adds(rowHalf_[co * chunkMax], rowHalf_[co * chunkMax], bcoH,
                             static_cast<int32_t>(chunkMax));
                    // ...
                    Cast(planeT, rowHalf_, RoundMode::CAST_NONE, nAll);
```

bias 窗先整块 `Cast` 到 half（`biasHalf_` / `biasH`），再在半精度做 `Adds`，最后 `Cast` 回 fp32。flush 路径不需要额外改（bias 在 gemm 内已加）。

### host UB 预算

新增 half 缓冲计入 `perBand`/`ubNeed` 同形公式，防两检不一致。

## 设计决策

- **为什么在 V 管道内做往返**：`Cast(CAST_NONE)` 是 RNE，与 torch `.half()` 一致；一次 V 往返的代价小于把整个 kernel 改成 half 计算，也避免 half 累加的溢出/舍入链。
- **为什么 bias 也要 Q16**：H2 模型的 `Q16(s)+Q16(bias)` 是逐项舍入；只把 bias 留 fp32 会在 0.1 量级上差 1 ulp，matched 从 1.0 掉到 0.99。
- **为什么 Conv2D/depthwise 不做输出 H2**：它们的参考输出是 fp32，不做额外舍入；给它们加 H2 会引入 ~1e-3 的偏差。
- **当前方案路线档位**：`recommended_fastpath`（先探针、再对齐）。

## 系统信息

- 目标平台：Ascend310P3（DAV_2002 / dav-m200），CANN 9.0.0，torch_npu 2.9。
- 相关文件：`op_kernel/conv_standard_3d_v6_gemm.cpp`（H2 epilogue）、`op_kernel/conv_transpose2d.cpp`（H2 epilogue）、`op_kernel/conv_depthwise2d.cpp`（R4 的 QUANT_F16 补丁；V5 同形实现见 depthwise 战役记录）。
- 探针：单值 conv + `torch.equal(e.half().float(), e)` + H1/H2 模型对照。

## 完整代码

上文的 Before/After 是同一修复补丁的两个 hunk（After 含 `QUANT_F16` 常量声明与量化块，逐字摘录）；H2 epilogue 是 causal unit 摘录（省略号处为未改动上下文）。单值探针是自包含的 torch 代码，按“一个 tap = w_val / 输入全 1”构造即可。

## 性能影响

同一算子内部相对代价（310P，标准 `msprof quick` kernel 级 `Task_Duration`）：

- fp16 往返 + H2 epilogue 的额外 Cast/Adds 约 **3–5%**（相对纯 fp32 lane）；换来精度门从“系统性 FAIL”到 50/50 或 60/60。
- 参照路线：纯 fp32 lane（不量化）；来源平台：310P。

## 预防

- 310P conv 族任务开局先跑单值探针 + `torch.equal(e.half().float(), e)`；不要假设参考是精确 fp32。
- Conv2D/depthwise 与 Conv3D/ConvTranspose2d 的输出档位不同，不要一刀切加 H2。
- bias 必须与卷积和分别 Q16 后再相加；H1 不够。
- 候选侧权重/输入都要过 fp16；只量化权重会得到“部分 case 对、部分错”的指纹。

## 验证信号

来源：310P conv 精度修复轮的同一条开发轨迹（单条轨迹、单次上板；证据等级 tool_observed/artifact_verified）。

- 单操作数预探针（辅助；不能单独区分操作数量化与只量化输出）：权重与输入分别落在 fp16 RNE（0.123456789→0.12347412、0.30000001→0.30004883；RTZ/bf16/13bit 对不上）；两操作数量化确认由下条 H2 模型的 9/9 逐位命中承担。（来源平台：310P；证据等级：tool_observed）
- 纯 fp32 候选 vs fp64 ≈ 1e-7，eager vs fp64 ≈ 1.48e-3；fp16 操作数 + fp32 累加 vs eager ≈ 4.8e-7。（来源平台：310P；证据等级：tool_observed）
- H2 模型在 Conv3D 的全部失败 case（9/9）上 matched≈1.00000（8 个探针 case 为 1.00000、case 0 为 0.99997；最终报告按 1.00000 记）；ConvTranspose2d 同样逐位命中；四算子修复后精度：Conv2D 50/50、Conv3D 60/60、depthwise 50/50、ConvTranspose2d 50/50（各自测试集）。（来源平台：310P；证据等级：artifact_verified）

## 失效边界

- **CPU fp32/fp64 golden**：本卡只适用于 device eager 参考；CPU 真值不做 fp16 量化，套用会引入 ~1e-3 偏差。
- **C==1 depthwise 的 FRACTAL_Z**：torch_npu 会把 `(1,1,K,K)` 权重转成 FRACTAL_Z，裸指针 kernel 只读到 `w[0]`；这是另一个独立硬 bug（clone 物化/`npu_format_cast`），不要与本卡的 fp16 语义混为一谈。
- **bf16/fp8 输入**：本卡只验证 fp32/fp16 路径；bf16 的舍入档位不同，未验证。
- **探针构造**：单操作数/含 1 的探针不能区分“操作数量化”与“只量化输出”；默认 bias 未关闭会叠加到输出。两操作数量化的确认以 H2 模型逐位命中为准。
- **其它代际**：只验证 310P；其它代际的 eager conv 语义不同（未验证，推断不可迁移）。
- **未决项**：C==1 FRACTAL_Z 的完整触发条件（仅 C==1？K 任意？）与缓存安全写法未在本卡展开；见后续卡。

## 坏实践

- 把 eager 当精确 fp32，继续用 CPU fp64 做绑定参考；结果是“实现越准越失败”。
- 只给 Conv3D/ConvTranspose2d 加 H2，忘了 Conv2D/depthwise 的输出是 fp32；或者反过来。
- 只量化权重、不量化输入；指纹是部分 case 对、部分错。
- 用 H1（`Q16(s+bias)`）代替 H2；matched 停在 0.989–0.995。
- 用“另一个乘数为 1”的单操作数探针就宣布两个操作数都被量化；它无法区分操作数量化与只量化输出，且默认 bias 会干扰。必须用两个非平凡乘数 + `bias=False`/零 bias。

## 误诊

- 第一轮把 1e-3 的差归因为“cube 累加顺序”或“tiling 不对”，试了多种 K 分块；单值探针显示参考本身就是 fp16 化的。
- 第二轮只做了输入/权重的 fp16，输出仍是 fp32；Conv2D/depthwise 过了，Conv3D/ConvTranspose2d 仍差；`torch.equal(e.half().float(), e)` 才把输出档位分离出来。
