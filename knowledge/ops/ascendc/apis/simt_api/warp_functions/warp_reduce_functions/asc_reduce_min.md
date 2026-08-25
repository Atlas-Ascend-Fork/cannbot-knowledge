---
type: API
title: asc_reduce_min
description: 对Warp内所有活跃线程输入val求最小值。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_reduce_functions/asc_reduce_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_reduce_min

对Warp内所有活跃线程输入val求最小值。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_reduce_min(int32_t val)；inline uint32_t asc_reduce_min(uint32_t val)；inline float asc_reduce_min(float val) 等4种重载

参数：val（输入）：源操作数。

返回值：Warp内所有活跃线程输入val的最小值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [Warp Reduce类函数](warp_reduce_functions.md)（`related`）：Warp Reduce 总览说明归约结果广播到 Warp 所有 Lane；AscReduceMin 给出其中仅对活跃线程取最小值、并向所有活跃线程返回同一结果的精确执行合同。
- [asc_reduce_add](asc_reduce_add.md)（`related`）：AscReduceMin 是相同 Warp 归约契约的最小值变体，用于按聚合目标在 sum/min 间选型。
- [AscReduceMin](../../../simd_api/c_api/reg/reduce_compute/asc_reduce_min.md)（`same_topic`）：asc_reduce_min 与《AscReduceMin》的实质衔接是：asc_reduce_min 在同一 warp 的活跃线程间广播最小值；add/max 和 C API 对应入口共享 active-lane 契约，warp reduce 总览补充调用范围。
- [AscReduceMinDatablock](../../../simd_api/c_api/reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《asc_reduce_min》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](../../../simd_api/basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《asc_reduce_min》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
- [asc_reduce_max](asc_reduce_max.md)（`same_topic`）：asc_reduce_min 与《asc_reduce_max》的实质衔接是：asc_reduce_min 在同一 warp 的活跃线程间广播最小值；add/max 和 C API 对应入口共享 active-lane 契约，warp reduce 总览补充调用范围。
<!-- cannbot:related:end -->
