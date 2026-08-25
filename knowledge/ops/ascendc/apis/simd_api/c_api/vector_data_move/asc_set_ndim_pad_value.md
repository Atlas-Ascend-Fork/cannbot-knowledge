---
type: API
title: AscSetNdimPadValue
description: 设置asc_ndim_copy_gm2ub接口Padding的填充固定值。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/asc_set_ndim_pad_value.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscSetNdimPadValue

当asc_ndim_copy_gm2ub接口的padding_mode参数为true时，该值将设置为Padding的填充固定值。fp8_e8m0_t，fp8_e5m2_t，fp8_e4m3fn_t类型的数据需转换成int8_t类型后再调用本接口。
函数原型：void asc_set_ndim_pad_value(int8_t pad_value)
约束：需配合asc_ndim_copy_gm2ub使用。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscNdimCopyGm2ub](asc_ndim_copy_gm2ub.md)（`related`）：AscSetNdimPadValue 只在 AscNdimCopyGm2ub 开启 padding_mode 时生效，是该搬运的直接前置配置。
- [AscSetCopyPadVal](asc_set_copy_pad_val.md)（`same_topic`）：AscSetCopyPadVal 的核心契约是“配合asc_copy_gm2ub_align或asc_copy_ub2gm_align接口，设置搬运数据块左右两侧需要填补的数据值”；AscSetNdimPadValue 补充“设置asc_ndim_copy_gm2ub接口Padding的填充固定值”。
- [AscSetNdimPadCount](asc_set_ndim_pad_count.md)（`same_topic`）：《AscSetNdimPadValue》明确“设置asc_ndim_copy_gm2ub接口Padding的填充固定值。”；它与《AscSetNdimPadCount》的“设置asc_ndim_copy_gm2ub接口各个维度左右侧的padding元素个数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
