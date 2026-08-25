---
type: API
title: GetTensorC
description: Iterate后获取C矩阵分片，可输出到GM或UB，支持同步与异步两种模式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetTensorC.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetTensorC

Iterate后，获取一块或者两块C矩阵片，可以直接输出到GM tensor中，也可以输出到UB（VECIN）tensor中。当MatmulConfig参数中的ScheduleType取值为ScheduleType::INNER_PRODUCT时，获取一块C矩阵片；当MatmulConfig参数中的ScheduleType取值为ScheduleType::OUTER_PRODUCT时，获取两块C矩阵片。

函数原型：template <bool sync = true>

参数：
- sync：设置同步或者异步模式：同步模式设置为true；异步模式设置为false。
- c/co2Local（输出）：取出C矩阵到UB（VECIN）。不同型号支持的数据类型请参考支持的数据类型。不同型号支持的数据格式请参考支持的数据格式。
- gm（输出）：取出C矩阵到GM，数据格式可以为ND或NZ。不同型号支持的数据类型请参考支持的数据类型。

约束：
- 传入的C矩阵地址空间大小需要保证不小于baseM * baseN。
- 异步场景时，需要使用一块临时空间来缓存Iterate计算结果，调用GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过SetWorkspace接口进行设置。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。
