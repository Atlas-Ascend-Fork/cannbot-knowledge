---
type: API
title: AscFloat2half
description: 将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---


# AscFloat2half

将float类型数据转换为half类型，支持多种舍入模式：
函数原型：void asc_float2half(__ubuf__ half* dst, __ubuf__ float* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscFloat2bfloat16](asc_float2bfloat16.md)（`related`）：half 与 bfloat16 目标范围/精度不同，按目标 dtype 选择。
- [__float2half_rd_sat](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_float2half_rd_sat.md)（`related`）：AscFloat2half说明将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式；对__float2half_rd_sat而言，这些转换保持 float→half 的同一源目的类型，只切换饱和开关与 rd/rn/rna/ro/ru/rz 舍入；C API 是跨执行模型的对应能力。
- [__float2half_rna](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_float2half_rna.md)（`related`）：AscFloat2half说明将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式。
- [AscFloat2Half](../reg/data_type_convert/asc_float2half.md)（`same_topic`）：C Vector AscFloat2half 与 C Reg 版本执行同一 float→half 转换并支持多种舍入；前者处理 UB 指针/count，后者用 RegTensor+mask。
- [__float2half](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_float2half.md)（`same_topic`）：焦点处理float→half 的默认与显式舍入模式；AscFloat2half正文界定“将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式”。候选保持 float→half 类型对，只改变舍入方向或高阶/标量 API 入口。
- [__float2half_rn](../../../simt_api/math_functions/half_type/half_precision_conversion_functions/_float2half_rn.md)（`same_topic`）：焦点处理float→half RINT 转换及显式舍入/饱和变体；AscFloat2half正文说明“将 float 转换为 half，并支持 RINT、ROUND、FLOOR、CEIL、TRUNC 和 ODD 舍入模式”。候选保持 float→half 类型对，只改变 RINT/ROUND/FLOOR/CEIL/TRUNC/ODD 与饱和模式。
<!-- cannbot:related:end -->
