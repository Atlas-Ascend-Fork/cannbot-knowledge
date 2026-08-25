---
type: API
title: __bfloat162int_rz
description: 遵循CAST_TRUNC模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/__bfloat162int_rz.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# __bfloat162int_rz

遵循CAST_TRUNC模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
函数原型：int __bfloat162int_rz(const bfloat16_t x)
返回值：输入遵循CAST_TRUNC模式转换成的有符号整数。特别场景说明如下：
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscBfloat162Int32](../../../../simd_api/c_api/reg/data_type_convert/asc_bfloat162int32.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《AscBfloat162Int32》补充：将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
- [AscBfloat162int32](../../../../simd_api/c_api/vector_compute/asc_bfloat162int32.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《AscBfloat162int32》补充：将bfloat16_t类型数据转换为int32_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
- [__bfloat162int_rd](_bfloat162int_rd.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《__bfloat162int_rd》补充：遵循CAST_FLOOR模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_rn](_bfloat162int_rn.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《__bfloat162int_rn》补充：遵循CAST_RINT模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_rna](_bfloat162int_rna.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《__bfloat162int_rna》补充：遵循CAST_ROUND模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
- [__bfloat162int_ru](_bfloat162int_ru.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《__bfloat162int_ru》补充：遵循CAST_CEIL模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。
<!-- cannbot:related:end -->
