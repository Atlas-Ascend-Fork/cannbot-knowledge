---
type: API
title: asc_half2int4x2 (废弃)
description: 将half类型数据转为int4x2类型，并支持多种舍入模式，饱和/非饱和模式。 关于舍入模式和饱和/非饱和模式的详细说明，请参见舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_half2int4x2_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_half2int4x2 (废弃)

将half类型数据转为int4x2类型，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：half、int4x2_t。

约束：- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscHalf2int4](../../vector_compute/asc_half2int4.md)（`related`）：asc_half2int4x2 (废弃) 与《AscHalf2int4》的实质衔接是：废弃 half→int4x2 转换需对照 int4 逆转换、当前 half 整数转换和舍入/饱和语义迁移。
- [asc_int4x22half (废弃)](asc_int4x22half_deprecated.md)（`same_topic`）：asc_int4x22half (废弃) 与《asc_half2int4x2 (废弃)》的实质衔接是：该废弃接口把 packed int4x2 转 half；同源 bfloat16/int16、逆向转换、废弃接口表及当前 AscInt4ToHalf 用于迁移并核对 packed lane。
- [舍入模式与饱和模式](rounding_mode.md)（`same_topic`）：asc_half2int4x2 (废弃) 与《舍入模式与饱和模式》的实质衔接是：废弃 half→int4x2 转换需对照 int4 逆转换、当前 half 整数转换和舍入/饱和语义迁移。
<!-- cannbot:related:end -->
