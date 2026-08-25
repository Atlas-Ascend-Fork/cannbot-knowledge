---
type: API
title: GetDropOutMaxMinTmpSize
description: 用于获取DropOut Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/data_filter/GetDropOutMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetDropOutMaxMinTmpSize

用于获取DropOut Tiling参数。

函数原型：void GetDropOutMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- typeSize（输入）：计算的数据类型大小，half=2，float=4。
- isReuseSource（输入）：预留参数，暂未启用，保持默认值false即可。
- maxValue（输出）：输出DropOut接口所需的tiling信息（最大临时空间大小）。 说明：maxValue仅作为参考值，有可能大于Unified Buffer剩余空间的大小，该场景下，开发者需要根据Unified Buffer剩余空间的大小来选取合适的临时空间大小。
- minValue（输出）：输出DropOut接口所需的tiling信息（最小临时空间大小）。

返回值：GetDropOutMaxTmpSize返回DropOut接口能完成计算所需最大临时空间大小。

<!-- cannbot:related:start -->
## 相关

- [DropOut](drop_out.md)（`same_topic`）：GetDropOutMaxMinTmpSize 与《DropOut》的实质衔接是：GetDropOutMaxMinTmpSize 给 DropOut kernel 分配可用临时空间，两者必须以相同 shape/type 契约调用。
<!-- cannbot:related:end -->
