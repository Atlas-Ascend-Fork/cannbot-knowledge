---
type: API
title: AscInt162half
description: 将int16_t类型数据转换为half类型，支持多种舍入模式： - 不指定舍入模式：无舍入。 - RINT舍入模式：四舍六入五成双舍入。
  - ROUND舍入模式：四舍五入舍入。 - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_int162half.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscInt162half

将int16_t类型数据转换为half类型，支持多种舍入模式：
函数原型：void asc_int162half(__ubuf__ half* dst, __ubuf__ int16_t* src, uint32_t count)
约束：dst、src的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscInt162Half](../reg/data_type_convert/asc_int162half.md)（`same_topic`）：《AscInt162half》处理“将int16_t类型数据转换为half类型，支持多种舍入模式： - 不指定舍入模式：无舍入。 - RINT舍入模式：四舍六入五成双舍入。 - ROUND舍入模式：四舍五入舍入。 - FLOOR舍入模式：向负无穷舍入。 - CEIL舍入模式：向正无穷舍入。 - TRUNC舍入模式：向零舍入。”。《AscInt162Half》提供“将src中int16_t类型的元素转换为half类型（16位浮点数），并将结果写入dst。源操作数和目的操作数位宽相同，转换后元素数量不变。支持5种舍入模式，关于舍入模式的详细说明请参见舍入模式与饱和模式。”，其具体合同或探针直接接入int16 到 half 的 C 与 C++ 等价转换合同。
<!-- cannbot:related:end -->
