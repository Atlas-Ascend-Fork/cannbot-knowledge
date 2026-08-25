---
type: API
title: asc_bfloat162e1m2x2 (废弃)
description: 将bfloat16_t类型转化为fp4x2_e1m2_t类型，并支持多种舍入模式。 关于舍入模式的详细说明，请参见舍入模式。 由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_bfloat162e1m2x2_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_bfloat162e1m2x2 (废弃)

将bfloat16_t类型转化为fp4x2_e1m2_t类型，并支持多种舍入模式。

关于舍入模式
由于源操作数与目的操作数类型位宽比为4:1，写入数据时需要将一个VL大小的数据分为四部分，根据不同接口选取索引0、索引1、索引2或者索引3。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、fp4x2_e1m2_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Float](asc_bfloat162float.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《AscBfloat162Float》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [AscFloat2Bfloat16](asc_float2bfloat16.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《AscFloat2Bfloat16》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_bfloat162e2m1x2 (废弃)](asc_bfloat162e2m1x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《asc_bfloat162e2m1x2 (废弃)》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_e1m2x22bfloat16 (废弃)](asc_e1m2x22bfloat16_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《asc_e1m2x22bfloat16 (废弃)》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_e2m1x22bfloat16 (废弃)](asc_e2m1x22bfloat16_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《asc_e2m1x22bfloat16 (废弃)》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [asc_int4x22bfloat16 (废弃)](asc_int4x22bfloat16_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《asc_int4x22bfloat16 (废弃)》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《废弃接口》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [类型转换](data_type_convert.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《类型转换》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [舍入模式与饱和模式](rounding_mode.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《舍入模式与饱和模式》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
<!-- cannbot:related:end -->
