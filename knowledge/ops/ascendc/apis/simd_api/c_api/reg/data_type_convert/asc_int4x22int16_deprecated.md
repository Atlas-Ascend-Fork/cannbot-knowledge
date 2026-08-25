---
type: API
title: asc_int4x22int16 (废弃)
description: 将int4x2_t类型转化为int16_t类型。 由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int4x22int16_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_int4x22int16 (废弃)

将int4x2_t类型转化为int16_t类型。

由于源操作数与目的操作数类型位宽比为1:4，读取数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：int16_t、int4x2_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [asc_int4x22half (废弃)](asc_int4x22half_deprecated.md)（`same_topic`）：asc_int4x22half (废弃) 与《asc_int4x22int16 (废弃)》的实质衔接是：该废弃接口把 packed int4x2 转 half；同源 bfloat16/int16、逆向转换、废弃接口表及当前 AscInt4ToHalf 用于迁移并核对 packed lane。
<!-- cannbot:related:end -->
