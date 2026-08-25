---
type: API
title: __bfloat162int_rd
description: 遵循CAST_FLOOR模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162int_rd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162int_rd

遵循CAST_FLOOR模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
函数原型：int __bfloat162int_rd(const bfloat16_t x)
返回值：输入遵循CAST_FLOOR模式转换成的有符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Int32](../../../../simd_api/c_api/reg/data_type_convert/asc_bfloat162int32.md)（`related`）：AscBfloat162Int32说明将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
- [AscBfloat162int32](../../../../simd_api/c_api/vector_compute/asc_bfloat162int32.md)（`same_topic`）：AscBfloat162int32 与《__bfloat162int_rd》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_rn](_bfloat162int_rn.md)（`same_topic`）：__bfloat162int_rn说明遵循CAST_RINT模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_rna](_bfloat162int_rna.md)（`same_topic`）：__bfloat162int_rna说明遵循CAST_ROUND模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_ru](_bfloat162int_ru.md)（`same_topic`）：__bfloat162int_rd说明遵循CAST_FLOOR模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_rz](_bfloat162int_rz.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《__bfloat162int_rd》补充：遵循CAST_FLOOR模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162uint_rd](_bfloat162uint_rd.md)（`same_topic`）：__bfloat162uint_rd 与《__bfloat162int_rd》的衔接是：这些接口都把浮点半精度值转为无符号整数，候选分别对比源类型及 rn/rd/ru/rz 舍入方向，可直接核对边界输入的转换结果。
- [__half2int_rd](../../half_type/half_precision_conversion_functions/_half2int_rd.md)（`same_topic`）：__half2int_rd 与《__bfloat162int_rd》的实质衔接是：这些卡保持 half 到整数转换并切换 rd/rn/rna/ru/rz 或目标有无符号；C 的 half2int16/32 入口说明向量执行层的目标位宽选择。
<!-- cannbot:related:end -->
