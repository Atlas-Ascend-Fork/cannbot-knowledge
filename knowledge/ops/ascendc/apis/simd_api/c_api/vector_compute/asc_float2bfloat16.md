---
type: API
title: AscFloat2bfloat16
description: 将float类型数据转换为bfloat16_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入
  - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_float2bfloat16.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscFloat2bfloat16

将float类型数据转换为bfloat16_t类型，并支持多种舍入模式：
函数原型：void asc_float2bfloat16_rn(__ubuf__ bfloat16_t* dst, __ubuf__ float* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [bf16 边缘失败用 fair-oracle 探针判 oracle 不公](../../../../runbooks/precision/bf16_fair_oracle_oracle.md)（`exemplifies`）：该卡若在候选外则可用于 bfloat16 输入量化后的公平 oracle。
- [AscFloat2Bfloat16](../reg/data_type_convert/asc_float2bfloat16.md)（`related`）：The Memory-vector C API performs the same float-to-bfloat16 conversion over UB arrays, complementing the focal register conversion.
- [AscFloat2half](asc_float2half.md)（`related`）：half 与 bfloat16 目标范围/精度不同，按目标 dtype 选择。
- [__float2bfloat16](../../../simt_api/math_functions/bfloat16_type/bfloat16_precision_conversion_functions/_float2bfloat16.md)（`same_topic`）：__float2bfloat16 的核心契约是“遵循CAST_RINT模式，将浮点数转换为bfloat16精度，返回转换后的值”；AscFloat2bfloat16 补充“将float类型数据转换为bfloat16_t类型，并支持多种舍入模式： - RINT舍入模式：四舍六入五成双舍入 - ROUND舍入模式：四舍五入舍入 - FLOOR舍入模式：向负无穷舍入 - CEIL舍入模式：向正无穷舍入 - TRUNC舍入模式：向零舍入”。
<!-- cannbot:related:end -->
