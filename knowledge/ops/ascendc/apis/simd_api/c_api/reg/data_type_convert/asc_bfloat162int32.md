---
type: API
title: AscBfloat162Int32
description: 将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_bfloat162int32.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscBfloat162Int32

将bfloat16_t类型数据转换为int32_t，并支持多种舍入模式，饱和/非饱和模式。

关于舍入模式和饱和/非饱和模式
由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器）。用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：bfloat16_t、int32_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 开启饱和模式和非饱和模式时，需配置ctrl寄存器，ctrl寄存器

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [__bfloat162int_rd](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rd.md)（`related`）：AscBfloat162Int32说明将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
- [__bfloat162int_rn](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rn.md)（`related`）：“__bfloat162int_rn”定义：遵循CAST_RINT模式，将bfloat16类型数据转换为有符号整数，返回转换后的值。；“AscBfloat162Int32”定义：将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。。实质衔接：这些接口保持 bfloat16→有符号整数任务，仅分别选择 ties-to-even、round-away 与 truncate；Reg C API 提供同目标类型的可配置舍入/饱和路径。
- [__bfloat162int_rna](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rna.md)（`related`）：C Reg 版本可批量执行相同 bfloat16→int32 转换，适合寄存器向量路径。
- [__bfloat162int_ru](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_ru.md)（`related`）：AscBfloat162Int32说明将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
- [AscBfloat162int32](../../vector_compute/asc_bfloat162int32.md)（`same_topic`）：AscBfloat162int32 与《AscBfloat162Int32》的衔接是：C Vector bfloat16 到 int32 的 rn 接口明确支持多种舍入模式；Reg 对应入口及 SIMT 的 rn/rd/ru/rz 变体用于逐模式核对结果。
- [__bfloat162int_rz](../../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_bfloat162int_rz.md)（`same_topic`）：__bfloat162int_rz：这些转换保持 bfloat16→int32 目标不变，只改变舍入模式或编程接口，能直接验证 rz 与 rd/rn/rna/ru 以及 C API 的行为差异。 目标卡《AscBfloat162Int32》补充：将bfloat16_t类型数据转换为int32_t，支持多种舍入模式和饱和/非饱和模式，源操作数与目的操作数位宽比为1:2。
<!-- cannbot:related:end -->
