---
type: Optimization
title: "X160: attention 前向按原生 stride 寻址，删除布局转换的全张量拷贝"
description: "评测/前向时间包含框架侧 permute+contiguous 辅助 kernel；当输入最后一维 stride==1 时，kernel 可直接按 (b,h,s) 原生 stride 寻址，host 不再物化连续布局，只下发 9 个 stride，wrapper 用 transpose 视图替代 permute+contiguous。可消除多次全张量拷贝，且数值逐位不变；最后一维不连续或不支持 stride 参数时不可用。"
tags:
  - task.optimization
  - topic.attention
  - topic.data_movement
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p157_native_stride_addressing
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/blob/51687dcbebee726b8c17c282ea6b02e19c6a23dd/knowledge/contrib/ascendc/optimizations/evolution_strategies/cards/p157_native_stride_addressing.md
    role: evidence
  - resource: https://gitcode.com/cann/cannbot-skills/blob/9e6774cef47d8bc483ac83de3eb0620a740d042a/community/ops/ascendc-evolution-strategies/references/preconditions/P157.yaml
    role: constraint
created_at: "2026-10-28T20:30:00Z"
updated_at: "2026-11-03T15:14:30Z"
platforms:
  - a2
  - a3
---
# X160: attention 前向按原生 stride 寻址，删除布局转换的全张量拷贝

> 已晋升为 [P157](../cards/p157_native_stride_addressing.md)。本卡保留为发现记录。
>
> P 卡当前状态：`draft`（待实际算子正确性/性能验证证据）。

## 核心思路
评测口径（例如 ops-profiling quick 的 Task Duration）把**一次前向里所有 AI_CORE/AIV/MIX kernel 求和**，所以框架侧为"把 BNSD 转成 kernel 期望的连续布局"而做的 `permute(...).contiguous()` 是三个全张量拷贝 kernel，在逐 case 时间上是真金白银。

只要输入的**最后一维（head dim D）stride == 1**，kernel 就不需要连续布局：把 `(b,h,s)` 三个轴的 stride 原样下发，GM 基址与行距改用 stride 表达式即可。取值集合与每个输出元素的运算链完全不变（逐位等价）。python 封装侧把 `permute(0,2,1,3).contiguous()` 换成 `transpose(1,2)` 得到零拷贝视图。

## 适用场景
- attention / GEMM 前向，输入布局与 kernel 内部行主序不同（如 BNSD vs BSH/BSND），且 D 轴连续。
- 判据：msprof 逐 kernel 表或 task_time.csv 显示 permute/contiguous/copy 类辅助 kernel 合计占前向不可忽略的比例。
- 反面：最后一维不连续（如 D 轴被切分/交错）时不可用，仍需物化。

## 实现要点
1. host：不再 `at::contiguous()`，只校验最后一维 `stride == 1`；把 9 个 int64 stride（`q_b/q_s/q_h`、`k_b/k_s/k_h`、`v_b/v_s/v_h`）随 TilingData 下发。
2. kernel：`q_base = bz*q_b + s0*q_s + hq0*q_h`；`kv_base = bz*k_b + nkv*k_h`；V 用独立的 `v_s` 做 tile 步进（`t*BLOCK_N*v_s`）；**输出仍写 kernel 内部连续张量**，其 base 单独保留原公式。
3. python 封装：`_to_bsnd` 的 BNSD 分支 `permute(0,2,1,3).contiguous()` → `transpose(1,2)`；BSH 的 `reshape+contiguous`、BSND 的 `contiguous` 本就是视图/空操作，保持不动。
4. 精度论证：BSH/BSND 的 stride 与原公式相等（`s = Hq*D, h = D, b = Sq*Hq*D`）→ 设备端逐字节不变；BNSD 只是"先转置成连续内存再按 BSH 读"换成"直接按 BNSD 步长读"。
5. 陷阱：不要为了省一次 `zeros(1)` 而跨调用缓存 1 元素占位 mask。跨调用缓存会把上一次的 device 状态带进下一次，可能造成明显回归；必须回退。
6. stride 下发的字段数量与顺序要和 kernel 侧完全一致；host 侧最好用一个结构体集中打包，避免参数错位。

## 边界
- 若 D 轴 stride != 1，或框架层会在 kernel 前后插入其它布局转换，本方案不成立。
- 若 kernel 内部某些 DMA 依赖连续行（例如整行 `DataCopy`），改成 stride 寻址后要确认这些 DMA 的源地址/行距仍正确。
- 输出连续假设不变；若输出也要按原生 stride 写，需单独验证。

## 验证方法
- 同窗口 A/B：BNSD/BSH/BSND 三种布局分别跑；BSH/BSND 应逐位不变。
- 用 msprof 确认辅助 copy kernel 消失。
- 逐 case 对比输出；重点看非连续输入与边界 shape。

## 关联
- 与 [X173](disc_x173.md)（head-major K/V 布局）同属"布局决定 DMA 形状"的路线：X160 是零拷贝视图，X173 是显式转置换连续 burst。
- 与 [X179](disc_x179.md)（转置放 wrapper 还是 kernel）配合做端到端带宽账。
