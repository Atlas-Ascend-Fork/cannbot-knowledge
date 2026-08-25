---
type: API
title: asc_reduce_max
description: 对Warp内所有活跃线程输入的val求最大值。Warp内所有活跃线程返回相同的结果。
tags: [task.lookup, topic.programming_model.cooperative_groups]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/Warp_functions/Warp_reduce_functions/asc_reduce_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_reduce_max

对Warp内所有活跃线程输入的val求最大值。Warp内所有活跃线程返回相同的结果。

函数原型：inline int32_t asc_reduce_max(int32_t val)；inline uint32_t asc_reduce_max(uint32_t val)；inline float asc_reduce_max(float val) 等4种重载

参数：val（输入）：源操作数。

返回值：Warp内所有活跃线程输入val的最大值。

仅 Ascend 950PR/950DT 支持，其他 Atlas 系列产品不支持。
需包含头文件 "simt_api/device_warp_functions.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。

<!-- cannbot:related:start -->
## 相关

- [AscReduceMax](../../../simd_api/c_api/reg/reduce_compute/asc_reduce_max.md)（`related`）：asc_reduce_max 与《AscReduceMax》的实质衔接是：Warp reduce max 与 min/add、C API 对应入口共享 warp 归约契约；padding 元素故障直接约束有效参与数。
- [ReduceMax接口](../../../simd_api/adv_api/reduction_operations/reduce_max_interface/reduce_max_interface.md)（`related`）：asc_reduce_max说明对Warp内所有活跃线程输入的val求最大值。Warp内所有活跃线程返回相同的结果。
- [Warp Reduce类函数](warp_reduce_functions.md)（`related`）：AscReduceMax 实现同一活跃线程归约契约的最大值聚合。
- [asc_reduce_add](asc_reduce_add.md)（`related`）：AscReduceMax 共享 Warp 活跃线程集合、全 lane 返回同一结果和树形归约模型，仅聚合算子由求和改为最大值。
- [asc_reduce_min](asc_reduce_min.md)（`same_topic`）：asc_reduce_min 与《asc_reduce_max》的实质衔接是：asc_reduce_min 在同一 warp 的活跃线程间广播最小值；add/max 和 C API 对应入口共享 active-lane 契约，warp reduce 总览补充调用范围。
<!-- cannbot:related:end -->
