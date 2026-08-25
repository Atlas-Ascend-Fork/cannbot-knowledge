---
type: API
title: AscSetNdimPadCount
description: 设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ndim_pad_count.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetNdimPadCount

用于设置asc_ndim_copy_gm2ub接口的各个维度左右侧的padding元素个数。
函数原型：void asc_set_ndim_pad_count(asc_ndim_pad_count_config& config)
约束：需配合asc_ndim_copy_gm2ub使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscNdimCopyGm2ub](asc_ndim_copy_gm2ub.md)（`related`）：AscSetNdimPadCount 配置各维 padding 个数，决定 AscNdimCopyGm2ub 写入 UB 时的补齐布局。
- [AscSetNdimLoopStride](asc_set_ndim_loop_stride.md)（`related`）：《AscSetNdimLoopStride》明确“设置asc_ndim_copy_gm2ub接口每个维度内源和目的操作数元素间的间隔，最多5个维度。”；它与《AscSetNdimPadCount》的“设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscNdimPadCountConfig](../struct/asc_ndim_pad_count_config.md)（`same_topic`）：《AscNdimPadCountConfig》明确“用于设置asc_ndim_copy_gm2ub接口各维度左右侧的padding元素个数。”；它与《AscSetNdimPadCount》的“设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscSetNdimPadValue](asc_set_ndim_pad_value.md)（`same_topic`）：《AscSetNdimPadValue》明确“设置asc_ndim_copy_gm2ub接口Padding的填充固定值。”；它与《AscSetNdimPadCount》的“设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
