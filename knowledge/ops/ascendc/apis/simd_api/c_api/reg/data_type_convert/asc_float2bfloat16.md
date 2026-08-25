---
type: API
title: AscFloat2Bfloat16
description: 根据mask将src中的float类型数据转换为bfloat16_t类型，支持多种舍入模式与饱和模式，结果写入dst，位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_float2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscFloat2Bfloat16

根据mask将src中的每个float类型数据转换成bfloat16_t类型，并支持多种舍入模式与饱和模式，结果写入dst。
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。伪代码
关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：bfloat16_t、float。

约束：- src与dst的数据类型需要与函数原型匹配。
- mask掩码位为0时，dst对应元素置0。
- 结果写入dst的奇数索引位置时，偶数索引位置置0；结果写入偶数索引位置时，奇数索引位置置0。
- 使用饱和或非饱和模式时，需要配置ctrl寄存器，详细说明

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2bfloat16](../../vector_compute/asc_float2bfloat16.md)（`related`）：The Memory-vector C API performs the same float-to-bfloat16 conversion over UB arrays, complementing the focal register conversion.
- [__float2bfloat16_ru_sat](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_float2bfloat16_ru_sat.md)（`related`）：《AscFloat2Bfloat16》明确“根据mask将src中的float类型数据转换为bfloat16_t类型，支持多种舍入模式与饱和模式，结果写入dst，位宽比为2:1。”；它与《__float2bfloat16_ru_sat》的“饱和模式下，将浮点数转换为bfloat16精度，并遵循CAST_CEIL模式，返回转换后的值。”在实际调用参数、数据流或结果校验上直接衔接。
- [asc_bfloat162e1m2x2 (废弃)](asc_bfloat162e1m2x2_deprecated.md)（`related`）：asc_bfloat162e1m2x2 (废弃) 与《AscFloat2Bfloat16》的实质衔接是：该废弃转换与 E1M2/E2M1 逆转换、现行 BF16 转换及舍入/饱和规则共享明确的位宽压缩与迁移契约。
- [__float2bfloat16](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_float2bfloat16.md)（`same_topic`）：AscFloat2Bfloat16 与 __float2bfloat16 都执行 float→bfloat16 转换；前者是带 mask 和可选舍入/饱和的 Reg 向量入口，后者是固定 CAST_RINT 的 SIMT 标量入口。
<!-- cannbot:related:end -->
