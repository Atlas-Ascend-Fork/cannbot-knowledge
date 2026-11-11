---
type: Optimization
title: "纯向量算子显式声明 AIV_ONLY task type（消除默认 MIX 编译带来的空转 AIC 派发）"
description: "用 `<<<blockDim, nullptr, stream>>>` 直编的 AscendC 工程中，`__global__ __aicore__` 内核若未显式声明 task type，会被编成 MIX 内核（同一符号同时存在 AIC/AIV 两份 meta 与机器码），纯向量算子因此多派发一整波空转 AIC block。显式声明 AIV_ONLY 可消除该派发开销。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X75: 纯向量算子声明 AIV_ONLY

## 核心思路

用 `<<<blockDim, nullptr, stream>>>` 直编（bisheng `-xasc`）的 AscendC 工程里，`__global__ __aicore__`
内核若**没有显式声明 task type**，会被编成 **MIX 内核**（编译产物里同一符号同时存在 `*_mix_aic` 与
`*_mix_aiv` 两份 meta 与两份机器码）。对**纯向量/MTE 算子**（只用 Max/Maxs/Cast/Brcb/Duplicate/DataCopy，
无 Cube/Fixpipe/L1、无 `g_coreType` 分支）来说，这等于每次 launch 都多派发**一整波无活可干的 AIC (cube) block**，
并让 AIV 那一半被 mix 派发/调度记账拖住。

在全部 kernel 入口首行加一行宏即可消除：

```cpp
template <typename T>
__global__ __aicore__ void my_kernel(...) {
    KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIV_ONLY);   // ← 纯向量算子必加
    ...
}
```

Block index 语义不变（`GetBlockIdx()` 仍是向量核上的 0..blockDim-1），**tiling / 分块 / UB 布局全都不用动**——
收益纯粹来自派发开销的消除。

## 适用场景

- **CANN 直编（`<<<>>>` + `--npu-arch`/`-xasc`）的 AscendC 工程**，且内核是纯向量/MTE 形态
  （逐元素、广播、cvt、纯向量 reduce；无 mmad/Fixpipe）。
- 症状自检：检查编译产物中同一 kernel 符号是否存在 `_mix_aic`/`_mix_aiv` 两份 meta，
  且内核确无 Cube 代码 → 命中。
- 收益形状：**每 block 有固定派发成本**，故收益与 block 数近似成正比；小 shape（launch 主导）
  相对收益最大，大 shape（带宽主导）收益占比下降。
- 不适用：真正含 Cube 的内核（应用 X24 的 `KERNEL_TYPE_AIC_ONLY`，方向相反）；
  用 `REGIST_MATMUL_OBJ`/KFC 框架注册的内核（task type 由框架决定）；
  纯标量 UB GetValue/SetValue 算子套 AIC_ONLY 会精度失败，但 **AIV_ONLY 对它们同样安全**。

## 实现要点

- 检查（改动前）：每个入口/实例在编译产物中出现两份 meta（`_mix_aic` 与 `_mix_aiv`）；
  改动后只剩 1 份，无 `_mix_*` 后缀。
- **模板入口要逐入口加**：`__global__` 模板的每个入口（通用/同形/单行B/广播）都要加，否则未声明的入口仍走 MIX。
- 宏定义在 AscendC 的 `kernel_utils_macros.h`
  （`KERNEL_TASK_TYPE_DEFAULT(value)` → `ENABLE_FEATURE_FOR_COMPILE(default, value)`）。
- 与 X24 是同一根因（**task type 必须显式声明**）的两个相反方向：
  计算落 Cube → AIC_ONLY；计算落 Vector → AIV_ONLY。

## 验证方法
- **性能**：在目标设备上对父变体与变体做同一时间窗口的 A/B（正反序至少两轮），
  按配对绝对时延判断，不用跨 run 比值（并发环境下漂移大）。
- **精度**：跑全量精度用例，逐元素对比参考实现；纯向量算子要求逐 bit 一致。
- **容量**：task type 改动不改变 tiling/UB 布局；仍建议审计 UB/L1/L0C/workspace 预算，
  确认无越界或静默覆写。
