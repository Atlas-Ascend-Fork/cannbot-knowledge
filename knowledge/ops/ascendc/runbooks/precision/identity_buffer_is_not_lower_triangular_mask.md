---
type: Runbook
title: 常量三角矩阵必须整块构建，只写主对角会退化成单位阵
description: 用 Duplicate(0) 加逐点 SetValue 构建下三角常量矩阵时只写了主对角，实际得到单位阵；改用逐行 Select 从全 1 张量裁剪。
tags: [task.debugging, topic.precision, topic.implementation.masking]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/SetValue.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
    role: supporting
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-31T09:21:53Z"
platforms: ["310p"]
---

# 常量三角矩阵必须整块构建，只写主对角会退化成单位阵

## 现象

为把门控前缀和立方化（`gk = Ltri @ g_row`，`g_row` 为每行的门控值广播），kernel 启动时构建一个 `[64,64]` 的“下三角含对角全 1”常量矩阵并常驻 L0A。首版这样写：

```cpp
        Duplicate(zeros8, static_cast<int8_t>(0), TILE);
        Duplicate(staging, static_cast<half>(0.0f), TILE);
        for (int32_t i = 0; i < T64; ++i) {       // 想写下三角含对角
            staging.SetValue(i * T64 + i, static_cast<half>(1.0f));
        }
```

意图是“先清零，再把下三角（含对角）置 1”，但循环体实际只写了 `(i,i)` 这些点——**得到的是单位阵 `I`**，不是下三角矩阵。后果：`gk = I @ g_row` = `g_row`，即每行等于该行自己的门控值，前缀和完全没有发生。

实测 dump（`gk` 与参考实现的逐元素比对，强门控用例第 0 个 chunk）：

```
gk[0] kern=-0.6426 ref=-0.6426
gk[1] kern=-1.1016 ref=-1.7439
gk[2] kern=-0.8525 ref=-2.5965
gk[3] kern=-0.5317 ref=-3.1280
gk[7] kern=-1.2500 ref=-5.8395
gk[15] kern=-0.8101 ref=-10.1285
gk[31] kern=-0.3552 ref=-17.4597
gk[63] kern=-0.3591 ref=-35.8324
```

`kern gk[i]` 恰好等于单个 token 的门控值（例如 `gk[1]=-1.1016` 就是该行自己的门控值），而 ref 是累加值——一眼可判“乘的是单位阵”。

## 适用场景

- 工程形态：AscendC kernel 直调，需要常驻 L0A/L1 的常量矩阵（三角、单位阵、掩码）。
- API 路径：`Duplicate`/`Select`/`Cast`（Vector）、`pushAt`（MTE3 推槽）、`Mmad`。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：operator_family（任何需要常量结构矩阵的立方 kernel）。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：本卡的掩码槽 `m0`/`m1` 是 `[64,64]` int8、按 64B 行距摆放，因此必须逐行 `Select`；若要改成整块 `Select`，掩码需重排为连续的 `count/8` 字节位流（见同批“整块 Select 的掩码必须连续位打包”卡）。本卡不适用于“稀疏到只需对角”的情形（那时单位阵就是想要的）。

## 判别方法

**根因**：`SetValue` 是标量写，循环只覆盖主对角；而下三角矩阵需要 `i >= j` 的全部位置。这个错误之所以难发现，是因为**单位阵与下三角矩阵在第 0 行、以及对角线上完全相同**，且“单个门控值本身看起来是合理的”（不是 NaN/0），所以不会在形状或数值范围上暴露，只会在前缀和结果里表现为“少了累加”。

## 解决配方

**before（错误，verbatim）**：见“现象”中的 `Duplicate(0)` + `for (i) SetValue(i*64+i, 1)`。

**after（用 per-row `Select` 从全 1 张量裁剪，verbatim）**：

```cpp
        // f32 0/1 掩码（m0/m1 按 64B 行距摆放, 故逐行 Select; 整块需连续位打包掩码）
        //   → f16 槽: 下三角 / 严格下三角 / 单位阵
        LocalTensor<float> onesR = tD;
        LocalTensor<float> zerosR = t2;
        Duplicate(onesR, 1.0f, T64);
        Duplicate(zerosR, 0.0f, T64);
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], m0[i * T64], onesR, zerosR,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);   // m0f → lf
            Select(vn[i * T64], m1[i * T64], onesR, zerosR,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);   // m1f → vn
        }
        PipeBarrier<PIPE_ALL>();
        Cast<half, float>(staging, lf, RoundMode::CAST_NONE, TILE);   // 下三角
        Cast<half, float>(staging2, vn, RoundMode::CAST_NONE, TILE);  // 严格下三角
        Sub(lf, lf, vn, TILE);   // 单位阵
        PipeBarrier<PIPE_ALL>();
```

要点：用 int8 掩码槽 `m0`（含对角下三角）/`m1`（严格下三角）逐行 `Select` 出 0/1 的 f32 掩码，再由 `Cast` 得到 f16 的下三角/严格下三角；单位阵由 `Sub(下三角 − 严格下三角)` 得到，**不用任何标量对角写**。槽位推送（每 kernel 一次）：

```cpp
    // ---- 常量三角/单位阵槽（每 kernel 一次）----
    pushAt(A_LTRI, staging, TILE * 2 / 32);
    pushAt(A_M1, staging2, TILE * 2 / 32);
    {
        drain3V();
        Cast<half, float>(staging, lf, RoundMode::CAST_NONE, TILE);  // 单位阵 f32
        pushAt(A_EYE, staging, TILE * 2 / 32);
    }
```

同一个坑在 `I − M` 的构造里也出现过（另一处标量对角写）：

```cpp
            Duplicate(vn, 0.0f, TILE);
            Muls(vn, lf, -1.0f, TILE);  // -M
            for (int32_t i = 0; i < T64; ++i) {
                vn.SetValue(i * T64 + i, 1.0f);   // I - M
            }
```

改为“加载单位阵槽 → `Cast` → `Sub`”：

```cpp
            {   // vn = I - M（单位阵槽 → f32 → Sub; 免标量对角写）
                DataCopy(staging, gmScr[scr + A_EYE],
                         DataCopyParams(TILE * 2 / 32, 1, 0, 0));
                SetFlag<HardEvent::MTE2_V>(ev2V);
                WaitFlag<HardEvent::MTE2_V>(ev2V);
                Cast<float, half>(vn, staging, RoundMode::CAST_NONE, TILE);
                Sub(vn, vn, lf, TILE);
            }
```

修后复测同一 dump：

```
gk[0] kern=-0.6426 ref=-0.6426
gk[1] kern=-1.7441 ref=-1.7439
gk[2] kern=-2.5957 ref=-2.5965
gk[15] kern=-10.1250 ref=-10.1285
gk[63] kern=-35.8438 ref=-35.8324
```

## 设计决策

- 为什么改“整块构建”而不是“补写三角剩余元素”：补写仍是 2080 次标量写，既慢又对 MTE3 不可见；`Select` 一次 64 行整向量完成。
- 为什么同时把单位阵也做成槽：`I − M` 每 chunk 都要，加载槽 + `Sub` 比任何标量对角写都便宜且确定。
- 为什么掩码按 per-row 使用：本卡的掩码槽按 64B 行距摆放，整块 `Select` 会从基址连续读 `count/8` 字节、跨过行距而错位；逐行 `Select` 与掩码布局同粒度。这不是平台不支持整块 `Select`——连续位打包掩码下整块 `Select` 在同平台实测可用（见同批 A/B 卡）。
- 掩码槽 `A_M1` 同时也成为后续 `aq`/`lf` 三角化的掩码来源（加载 → `Cast` → `Mul`）。

## 系统信息

- toolchain：CANN 9.1.0，bisheng/ccec，`cmake` + `ascendc.cmake`，SOC_VERSION=Ascend310P3。
- 目标平台：Ascend310P3（dav-m200 / DAV_2002）。
- 槽位：`A_LTRI = 2*TILE`、`A_EYE = 22*TILE`、`A_M1 = 23*TILE`（scratch 视图，单位 tile = 4096 元素）。
- 掩码张量：`m0`/`m1` 为位打包的 int8 `[64,64]`（每元素 1 bit，每行行首 `T64/8` 字节有效），kernel 启动时由主机侧/常量化构造。

## 完整代码

完整因果单元为上面的 after 段（逐行 `Select` 构建下三角/严格下三角/单位阵 + 槽位推送）。可直接复用的完整实现：

```cpp
        LocalTensor<float> onesR = tD;
        LocalTensor<float> zerosR = t2;
        Duplicate(onesR, 1.0f, T64);
        Duplicate(zerosR, 0.0f, T64);
        for (int32_t i = 0; i < T64; ++i) {
            Select(lf[i * T64], m0[i * T64], onesR, zerosR,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
            Select(vn[i * T64], m1[i * T64], onesR, zerosR,
                   SELMODE::VSEL_TENSOR_TENSOR_MODE, T64);
        }
        PipeBarrier<PIPE_ALL>();
        Cast<half, float>(staging, lf, RoundMode::CAST_NONE, TILE);
        Cast<half, float>(staging2, vn, RoundMode::CAST_NONE, TILE);
        Sub(lf, lf, vn, TILE);
        PipeBarrier<PIPE_ALL>();
        pushAt(A_LTRI, staging, TILE * 2 / 32);
        pushAt(A_M1, staging2, TILE * 2 / 32);
        drain3V();
        Cast<half, float>(staging, lf, RoundMode::CAST_NONE, TILE);
        pushAt(A_EYE, staging, TILE * 2 / 32);
```

## 性能影响

本卡是正确性修复。相对代价：常量构建由“2080 次标量 `SetValue`”降为“64 次 per-row `Select` + 3 次 `Cast`”，且只在 kernel 启动时做一次（每 kernel 一次，非每 chunk），对 chunk 循环无成本。

## 预防

- 构造常量结构矩阵后，**必须 dump 并与参考实现逐元素比对**，尤其要 dump 第 1 行和第 30+ 行（首行往往两个候选矩阵相同）。
- 看到 `for (i) SetValue(i*N+i, 1)` 就意识到它是单位阵，不是三角阵。
- 常量矩阵一律整块构建（`Duplicate` + `Select`），不要用标量点写补洞。
- 数值“看起来合理”不是正确的证据：单位阵乘出来的就是原向量，量级与符号都正常。

## 验证信号

来源说明：本卡来自 Ascend310P3 会话内对门控前缀和向量的 device dump 与参考实现逐元素比对（修复前/后各一次）。

- 修复前：`gk[1..63]` 等于单 token 门控值而非前缀和（`gk[1] -1.1016` vs ref `-1.7439`）（来源平台：310P；证据等级：tool_observed）。
- 修复后：`gk[1] -1.7441` vs ref `-1.7439`、`gk[63] -35.8438` vs ref `-35.8324`（来源平台：310P；证据等级：tool_observed）。
- 有效证据只到上面的中间态 dump：该下三角变体随后与门控前缀和立方化方案一起被回退（终版改用向量前缀和，说明为“列广播/三角-Mmad 变体在强门控下漂移”），因此全套用例的通过/失败**不能归因于本修复**，不列为验证信号；“对角写 = 单位阵”这一根因本身与回退无关（来源平台：310P；证据等级：artifact_verified）。

## 失效边界

- 只在 Ascend310P3 + CANN 9.1.0 验证；`SETMODE` 枚举与掩码语义在 910B 上未验证。
- 本卡对应的下三角变体在会话后期已被回退（终版改用向量前缀和），没有留到终版；结论的有效范围是同会话中间态 dump 的二点对比，未经过完整回归。
- 本卡假设掩码张量 `m0`/`m1` 本身正确（由 host/初始化生成）；掩码若错，症状与“只写对角”类似。
- 若将来 tile 行数 ≠ 64，掩码、槽大小、per-row 循环都要同步重建。
- 未决项（优先）：标量对角写的失效是否仅因为“循环只覆盖对角”（逻辑错），还是同时叠加了“标量写对 MTE3 不可见”（时序错），本会话未做隔离实验；从后续 `I − M` 的同类错误看，两者可能同时存在。

## 坏实践

- `Duplicate(0)` + `for (i) SetValue(i*64+i, 1)` 声称构建了下三角矩阵。
- 用“第一行正确、对角线正确”判定常量矩阵正确。
- 在每 chunk 的循环里用标量写构造 `I − M`：既慢又不可见。

## 误诊

- 曾怀疑是 `Mmad` 的 A 槽装载（`Nd2Nz`/`LoadData3D`）把矩阵搬错了，于是去查搬运路径；实际上 A 槽内容就是单位阵，搬运没错。
