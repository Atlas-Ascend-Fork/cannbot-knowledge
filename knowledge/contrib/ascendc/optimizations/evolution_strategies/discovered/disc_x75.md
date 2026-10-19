---
type: Optimization
title: "纯向量算子显式声明 AIV_ONLY task type（消除默认 MIX 编译带来的空转 AIC 派发）"
description: "用 <<<blockDim, nullptr, stream>>> 直编（bisheng -xasc）的 AscendC 工程里，__global__ __aicore__内核若没有显式声明 task type，会被编成 MIX 内核（.so 里同一符号同时存在 _mix_aic 与_mix_aiv…"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement.layout_transform
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-10-13T00:00:00Z"
platforms:
  - a2
---

# Strategy X75: 纯向量算子声明 AIV_ONLY

> 进化发现元数据（迁移自 cannbot-skills `references/discovered/` 原始 frontmatter）：
>
> ```yaml
> schema_version: okf.v1
> kind: discovered_strategy
> id: X75
> title: "纯向量算子显式声明 AIV_ONLY task type（消除默认 MIX 编译带来的空转 AIC 派发）"
> origin: discovered
> discovered_round: 3
> discovered_from: "Maximum evolution, round_3/parallel_2 (node x0_x1, open_exploration)"
> base_speedup: "同 run geomean_speedup 0.9168 -> 1.1796；Σasc 2569.72 -> 2327.90us (-9.4%)；geomean_asc 64.49 -> 50.80us (-21.2%)；20/20 case 全部变快 (-2.1% ~ -40.0%)，20/20 逐位精度"
> confidence: single_op
> status: active
> op_families: [elementwise, broadcast, reduction]
> bottlenecks: [scalar_compute, no_overlap, mte2_stall, tiling_imbalance]
> tags: [task-type, aiv-only, mix-dispatch, launch-floor, dispatch-overhead, kernel-entry, cann-direct-launch, 910b2c, dav-c220, pure-vector]
> strategy_ids: [X75, X24, P54]
> ```

## 核心思路

用 `<<<blockDim, nullptr, stream>>>` 直编（bisheng `-xasc`）的 AscendC 工程里，`__global__ __aicore__`
内核若**没有显式声明 task type**，会被编成 **MIX 内核**（.so 里同一符号同时存在 `*_mix_aic` 与
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
- 症状自检（30 秒）：`strings <so> | grep -c '<kernel符号>_mix_aic'` > 0 且内核确无 Cube 代码 → 命中。
- 收益形状：**每 block 固定成本 ≈0.3-1.2us**，故 Δus 与 block 数近似成正比，
  小 case（launch 主导）相对收益最大（-30%~-40%），大 case（带宽主导）仍有 -2%~-12%。
- 不适用：真正含 Cube 的内核（应用 X24 的 `KERNEL_TYPE_AIC_ONLY`，方向相反）；
  用 `REGIST_MATMUL_OBJ`/KFC 框架注册的内核（task type 由框架决定）；
  纯标量 UB GetValue/SetValue 算子套 AIC_ONLY 会精度失败（见 f12），但**AIV_ONLY 对它们同样安全**。

## 实现要点

```cpp
// 检查（改动前）：每个入口/实例出现 2 份 meta
//   $ strings kernel/_pkg/cann_bench/_C.abi3.so | grep -oE 'ascend\.meta\.[^ ]*' | sort -u | head
//   ..._Z14maximum_kernelIDhEvPhS0_S0_ll..._mix_aic
//   ..._Z14maximum_kernelIDhEvPhS0_S0_ll..._mix_aiv
// 改动后：只剩 1 份，无 _mix_* 后缀
//   ..._Z14maximum_kernelIDhEvPhS0_S0_ll...
```

- **模板入口要逐入口加**：`__global__` 模板的每个入口（通用/同形/单行B/广播）都要加，否则未声明的入口仍走 MIX。
- 宏定义在 `${ASCEND_HOME_PATH}/<arch>/asc/impl/basic_api/utils/kernel_utils_macros.h`
  （`KERNEL_TASK_TYPE_DEFAULT(value)` → `ENABLE_FEATURE_FOR_COMPILE(default, value)`）。
- 与 X24 是同一根因（**task type 必须显式声明**）的两个相反方向：
  计算落 Cube → AIC_ONLY；计算落 Vector → AIV_ONLY。
- 落地后按「同窗配对绝对 asc / Σasc」验证，不要用跨 run geomean 比值（本机并发下漂移 ±30%）。

## 来源

自动发现于第 3 轮进化，算子 Maximum（cann-bench level2，纯访存 elementwise+broadcast，AIV-only，
4 个 kernel 入口，2693 行）。实测：Σasc 2569.72 → 2327.90us（-9.4%，3 次复现 2318/2328/2317），
geomean_speedup 0.9168 → 1.1796，20/20 case 全部变快，20/20 逐位精度 PASS。
