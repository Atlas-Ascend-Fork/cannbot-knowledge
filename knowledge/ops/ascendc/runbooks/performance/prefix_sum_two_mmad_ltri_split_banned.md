---
type: Runbook
title: 前缀和立方化到 Ltri@bcast：思路可行，强门控下漂移已回退
description: 逐行 Duplicate+Add 前缀和可降为常驻 Ltri 的两次 Mmad；本会话实测该变体在强门控用例上 gk 漂移，最终回退到向量前缀和。
tags: [task.optimization, topic.programming_model.execution_unit.cube, topic.programming_model.execution_unit.vector]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/data_move/DataCopy_GMAndUB_highdim_split.md
    role: constraint
created_at: "2026-10-28T09:46:50Z"
updated_at: "2026-10-28T09:46:50Z"
platforms: ["310p"]
---

# 前缀和立方化到 Ltri@bcast：思路可行，强门控下漂移已回退

## 现象

分块递推算子里每个 chunk 都要把 `[64]` 的门控标量 `g`（每行一个值）变成：

1. 行内前缀和 `gk_i = g_0 + … + g_i`（除以 ln2）；
2. 一个 `[64, K]` 的广播矩阵（每行常量 = `gk_i`），供后续逐元素 `Exp` 生成 `2^(gk_i−gk_j)` 型衰减。

首版实现（310P，kernel 直调）直接这样写：

```cpp
            // ---- 标量门 64×f32 → 广播 [64,128] → cumsum → gk ----
            DataCopy(tD, gmG[tBase], DataCopyParams(T64 * 4 / 32, 1, 0, 0));
            SetFlag<HardEvent::MTE2_V>(ev2V);
            WaitFlag<HardEvent::MTE2_V>(ev2V);
            for (int32_t r = 1; r < T64; ++r) {   // 先广播后累（行 0 保持源）
                Duplicate(gk[r * K128], tD.GetValue(r), K128);
            }
            Duplicate(gk, tD.GetValue(0), K128);
            for (int32_t r = 1; r < T64; ++r) {
                Add(gk[r * K128], gk[r * K128], gk[(r - 1) * K128], K128);
            }
            Muls(gk, gk, INV_LN2, T64 * K128);
```

即：64 次 `Duplicate`（每次一次标量 `tD.GetValue(r)`）+ 63 次 `Add` + 1 次整张量 `Muls`。`msprof` 显示该 kernel `vec_ratio≈0.43`、`scalar_ratio≈0.32`、`mac_ratio≈0.02`——立方几乎闲置，瓶颈就是这类“每行一次 V 调用 + 每行一次标量取值”的循环。

为了把这 127 次 V 调用压成立方调用，本会话实现了一个“`Ltri` 常驻 + hi/lo 两次 Mmad + 列广播”的变体：**弱门控用例上它是对的，强门控用例上却给出随运行而变的 `gk`**，最终整段被换回上面这段向量前缀和。本卡因此是“这个方向被证伪”的记录，而不是可照抄的配方。

## 适用场景

- 工程形态：AscendC kernel 直调（自写 kernel + torch.ops 绑定），Cube+Vector 混合流水。
- API 路径：`Duplicate`/`Add`/`Muls`/`Cast`/`Exp`（Vector）、`Mmad`/`LoadData`/`LoadData2D`/`Nd2Nz`（Cube/MTE1）；常量矩阵用 `Select`+`Duplicate` 构建后常驻 L0A。
- 验证过的平台与 CANN 版本：310P（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：operator_family（任何“逐行标量门 → 前缀和 → 广播矩阵”的 chunked recurrence 算子）。
- 路线优先级：banned（本会话实测该变体在强门控用例上 gk 漂移，已回退到向量前缀和 `Duplicate`+`Add`；基线即该向量版本）。
- 明确不适用 / 未验证场景：g 为 [64, K] 每列不同（非行常量）时，本配方的前缀和语义不再成立，应改用真正的矩阵 cumsum；`Transpose`/`Brcb` 在这条路径上未在 910B 验证（未验证，推断可迁移）。

## 根因 / 解决配方

**根因**：`Duplicate` 与 `Add` 都是按行的一次向量指令，64 行前缀和 = 127 次 V 调用 + 64 次标量 `GetValue`，指令条数与行数成正比，且标量取值在 V 管道上形成串行依赖。立方（Mmad）在这个循环里完全没被使用。

**尝试（该变体在本会话被回退，不可直接采用；结论见“设计决策”末条）**：把“前缀和 + 行广播”识别为**三角矩阵乘**：

- `Ltri` = 含对角的 `[64,64]` 下三角全 1 矩阵（每 kernel 构建一次，常驻 L0A 专用槽）；
- `g_bcast` = `g/ln2` 的行广播矩阵（每行常量）；
- `gk = Ltri @ g_bcast` —— 一次 Mmad 就得到行内前缀和，且结果天然是 `[64, K]` 广播矩阵。

难点是 `g_bcast` 本身要广播（不能再用 `DataCopy` 的 srcStride 技巧，见精度类卡：`DataCopy` 的 srcStride=0 不广播）。做法是 **hi/lo f16 拆位 + 两次 Mmad 累加**：把 f32 的 `g/ln2` 拆成 f16 高位 `hi` 与残差 `lo`，分别列广播成 `[64,64]`，用同一个 `Ltri` 连做两次 Mmad 累加，得到 f32 精度的 `gk`（避免 f16 直接量化门控值）。

**尝试实现（Process 内该段，verbatim；后被回退）**：

```cpp
            // ---- gk: g f32[64] → hi/lo f16 → 列广播 → Ltri@bcast ----
            DataCopy(tD, gmG[tBase], DataCopyParams(T64 * 4 / 32, 1, 0, 0));
            SetFlag<HardEvent::MTE2_V>(ev2V);
            WaitFlag<HardEvent::MTE2_V>(ev2V);
            Muls(t2, tD, INV_LN2, T64);                            // g/ln2
            Cast<half, float>(gH, t2, RoundMode::CAST_NONE, T64);  // hi
            Cast<float, half>(tD, gH, RoundMode::CAST_NONE, T64);
            Sub(t2, t2, tD, T64);                                  // 残差
            Cast<half, float>(gH[T64], t2, RoundMode::CAST_NONE, T64);  // lo
            PipeBarrier<PIPE_ALL>();       // V 写 → UB 拷贝（双端律）
            colBcast16(staging, gH);          // hi 列广播
            colBcast16(staging2, gH[T64]);    // lo 列广播
            pushAt(G_BH, staging, TILE * 2 / 32);
            pushAt(G_BL, staging2, TILE * 2 / 32);
            {   // 双 B 累加轮（A = Ltri 常驻）
                drain32();
                warm32(G_BH);
                warm32(G_BL);
                Nd2NzParams ndB = nd64;
                DataCopy(l1b, gmScr[scr + G_BH], ndB);
                DataCopy(l1b2, gmScr[scr + G_BL], ndB);
                SetFlag<HardEvent::MTE2_MTE1>(ev21);
                WaitFlag<HardEvent::MTE2_MTE1>(ev21);
                LoadData(l0bS0, l1b, pB64N);
                LoadData(l0bS1, l1b2, pB64N);
                SetFlag<HardEvent::MTE1_M>(ev1M);
                WaitFlag<HardEvent::MTE1_M>(ev1M);
                MmadParams mps = mpK64;
                mps.cmatrixInitVal = true;
                Mmad(l0c, l0aLT, l0bS0, mps);
                mps.cmatrixInitVal = false;
                Mmad(l0c, l0aLT, l0bS1, mps);
                PipeBarrier<PIPE_ALL>();
            }
            readout();
            DataCopy(gk, t2, DataCopyParams(TILE * 4 / 32, 1, 0, 0));
            SetFlag<HardEvent::MTE3_V>(ev3V);
            WaitFlag<HardEvent::MTE3_V>(ev3V);
```

`colBcast16`（列广播 [64]→[64,64] f16，随本方案一起引入，verbatim）：

```cpp
    // ---- 列广播 [64,64] f16（全行 = src[64] 向量; 探针 mode2/3/4 实证）----
    //   Brcb: [64] → bcT [64,16]（行 i = {v_i×16}）
    //   4× vtranspose（连续 16×16 tile, 就地转置到 bcT2）→ bcT2 行 16t+d = 段 t
    //   4 次 strided 拷贝（列 16t, 行距 4 块）→ dst [16,64] 头（全行 = v）
    //   3 次行块拷贝 → [64,64]
    LocalTensor<half> bcT = msBuf.Get<half>()[4 * 128 + 128];   // [64,16]
    LocalTensor<half> bcT2 = bcT[64 * 16];                       // [64,16]
    auto colBcast16 = [&](const LocalTensor<half>& dst,
                          const LocalTensor<half>& src) __aicore__ {
        Brcb<half>(bcT, src, 8, BrcbRepeatParams(1, 8));
        for (int32_t t = 0; t < 4; ++t) {
            Transpose<half>(bcT2[t * 256], bcT[t * 256]);
        }
        PipeBarrier<PIPE_ALL>();            // V 写 → UB 拷贝（双端律）
        for (int32_t t = 0; t < 4; ++t) {   // 段 t → dst 列 [16t,16t+16)
            DataCopy(dst[t * 16], bcT2[t * 256],
                     DataCopyParams(16, 1, 0, 3));
        }
        for (int32_t rr = 1; rr < 4; ++rr) {   // [16,64] → [64,64]
            DataCopy(dst[rr * 16 * T64], dst, DataCopyParams(16, 4, 0, 0));
        }
        PipeBarrier<PIPE_ALL>();
    };
```

`Ltri` 是“下三角含对角全 1”的常量矩阵，每 kernel 构建一次并常驻 L0A。它的构建必须用向量 `Select`（本会话里用 `Duplicate(0)`+`SetValue` 只写主对角的写法被实证是错的——那得到的是单位阵，立方输出就退化成 `g_i` 而不是前缀和）；完整 before/after 见精度类卡“Ltri 只写主对角”。

## 设计决策

- 为什么用“三角矩阵乘”而不是向量前缀和：`Ltri` 是常量，一次构建、常驻 L0A，可以每个 chunk 复用；一次 Mmad 把 127 次 V 调用压成 1 次立方调用，且立方当时是闲置资源（`mac_ratio≈0.02`）。
- 为什么 hi/lo 拆成两次 Mmad 而不是直接 f16 一次：门控值 f16 量化误差会在后续 `Exp(2^(gk_i−gk_j))` 里被指数放大；拆位后两次累加得到接近 f32 的乘积精度，代价只是第二次 Mmad（立方本来就是富余资源）。
- 为什么列广播不用 `DataCopy(srcStride=0)`：该写法并不广播（源地址每次步进 `blockLen+srcStride`），会读到错误数据；`Brcb`+`vtranspose`+MTE 重排是实测可用的替代。
- 放弃的候选：在 UB 里用 `Transpose`/`v4dtrans` 做整 `[64,64]` 转置来替代立方转置（见同批负结果卡，tile 语义不匹配）。
- 本会话结论（必读）：该变体实现后，弱门控用例上 `gk` 数值正确（`gk[1]` 与 ref 逐位吻合），但强门控用例上 `gk` 构建出现**非确定性错误**（同一份代码多次运行从第 0 行起就不同），且随后的 `gk` 列0 GM 往返与带划分都依赖它。排查未收敛到单一机制后，本会话把 `gk` 段整体换回旧的 `Duplicate`+`Add` 前缀和，最终 v2 的提交说明明确写“gk via proven Duplicate-broadcast + row-Add cumsum (colBcast/Ltri-Mmad variant drifted on strong gates)”。因此本卡记录的是**被证伪的优化方向**，不是可直接采用的配方。
- 路线优先级：banned。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：310P（dav-m200 / DAV_2002）。
- 目录布局：`kernel/<generic>.cpp`（kernel）、`host/<generic>_host.cpp`（torch.ops 绑定与预处理）、`build/`（产物）、`tests/test_<generic>.py`（精度门）。
- UB 预算：`pipe.InitBuffer(msBuf, 16 * 128 * sizeof(float))`（8KB 标量区），`colBcast16` 的 `bcT`/`bcT2` 放在该区尾部。
- 相关文件清单与事件流一致：kernel、host、tests、build.sh、CMakeLists.txt。

## 性能影响

本卡**没有**可归因到“前缀和立方化”这一项的实测收益：

- 同一算子内部成对对比（同一 msprof kernel Task_Duration 主口径、310P）显示整条 v2 路线相对旧逐行路线约 **1.4x**，但 v2 终版用的是**向量前缀和**（`Duplicate`+`Add`）+ 带状因子折进 A 操作数（另一卡），故这条相对收益不能算在本段头上。
- 本段只有指令数层面的定量：V 调用从 127 次（64 `Duplicate` + 63 `Add`）+ 64 次标量取值，降为 2 次 Mmad + 2 次列广播（每次列广播 = 1 Brcb + 4 vtranspose + 7 次 MTE 拷贝）。
- 也就是说，“用立方替代逐行前缀和”在指令数上明显更省，但本会话未能把它做成可通过强门控用例的实现——收益与代价都停在纸面。

## 预防

- 出现“每行一次 `Duplicate`/`Muls`/`Add`、每行一次 `GetValue`”的循环，先问能否写成常量矩阵乘（前缀和=下三角；差分=上三角；one-hot 选择=置换矩阵）。
- 广播到 `[64,64]` 的向量，别用 `DataCopy` 的 srcStride=0 假冒广播。
- 常量矩阵用 Select 构建时确认掩码是含对角还是严格下三角，本算子两个版本都要（`I` 与 `Ltri`）。

## 验证信号

来源说明：本卡来自一次 310P 算子优化会话；变体实现后在单个用例上 `gk` 数值正确，但强门控用例上 `gk` 构建出现非确定性错误，最终该段被回退。

- 变体实现后（弱门控用例）：`gk[1]`/`gk[63]` 与 ref 逐位吻合，hi/lo 拆位误差约 1e-2 绝对量级（来源平台：310P；证据等级：tool_observed）。
- 强门控用例：`gk` 从第 0 行起就与 ref 不符，且同一份代码多次运行的 dump 不一致（非确定性），进而 `kg` 饱和、末态发散（来源平台：310P；证据等级：tool_observed）。
- 回退证据：最终 v2 提交说明明确写“gk via proven Duplicate-broadcast + row-Add cumsum (colBcast/Ltri-Mmad variant drifted on strong gates)”，即该变体**未**进入终版（来源平台：310P；证据等级：artifact_verified）。
- 该回退版本的 50 例精度门 `50/50 PASS`、主口径 `COMPARE-EXIT=0`/valid 10/10，但用的是向量前缀和，**不能**作为本方案的有效性证据（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 310P + CANN 9.1.0 验证；`Ltri` 常驻 L0A 会占用 L0A 的一个 tile 槽，若 L0A 预算已满需改为按需 push（多一次 MTE1）。
- **强门控输入下不可用**（本卡被判 `banned` 的直接原因）：g 每 token 可达约 5 log2 时，该 gk 构建路径（hi/lo 拆位 + `colBcast16` 列广播 + 两次 Mmad）出现非确定性错误，弱门控用例不会触发。若要在强门控下复走此路线，必须先解决“列广播写/读竞争”（本会话仅怀疑 `colBcast16` 写 `staging` 与在飞 MTE3 读之间缺 drain，未证实）。
- `Ltri` 尺寸绑定 tile 行数（本实现为 64），换 tile 大小时必须重建常量矩阵与掩码。
- hi/lo 拆位要求 g 值域在 f16 可表示范围内（拆位后残差也很小）；若 g 的量级本身超出 f16 指数范围（强门），要先钳位（钳位本身会引入误差，见精度类卡的带跨度上限）。
- 未决项：
  - **复现并追根因到机制层**：强门控下 gk 非确定性漂移的机制未定位（怀疑 `colBcast16` 写 `staging` 与在飞 MTE3 读无 drain，但未隔离证实）；因此本卡只有“该变体不可用”的负结论，没有“如何修好它”的配方。
  - **复现并追根因到机制层**：本会话未单独测量“前缀和立方化”这一项相对旧路线的收益（与带因子折进 A 操作数同时上线），需逐手段消融；且该变体未进终版，收益无法复测。
  - `Brcb` 的 `dstRepStride` 与 tile 落位关系在本会话只按探针实测反推，未查文档确认通用形式；行数非 64 时需重新验证。

## 坏实践

- 用 `DataCopy(staging, gH, DataCopyParams(T64, 1, 0, 3))` 当列广播：逐块源地址推进 `1+3=4` 块，读到的是原数据的不同行，不是广播。本会话一度用它把 gk 列广播成垃圾。
- 在指针上直接 `DataCopy` 不同类型（float 缓冲 ← half GM）—— 需要 `ReinterpretCast<half>()`，否则重载匹配失败（编译错）。
- 全张量 `Select` 在 m200 上不可用（见精度类卡），构建三角掩码必须逐行。

## 误诊

- 曾认为 gk 广播错是“广播矩阵写错一列”，实际是 `DataCopy` srcStride 语义误解 + 标量读不到 V/MTE3 写的数据（两条独立根因）。
