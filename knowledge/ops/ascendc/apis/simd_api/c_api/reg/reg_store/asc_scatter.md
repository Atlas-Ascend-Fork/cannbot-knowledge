---
type: API
title: AscScatter
description: 根据索引值index将源操作数src中的元素分散存储到目的操作数dst中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/asc_scatter.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscScatter

该指令会根据索引值index将源操作数src中的元素分散到目的操作数dst中。分散过程
函数原型：void asc_scatter(__ubuf__ int8_t* dst, vector_int8_t src, vector_uint16_t index, vector_bool mask)
约束：dst首地址必须32B对齐。；当dst为int8_t或者uint8_t数据类型时，源操作数中仅偶数位元素有效。即src中的偶数位置[0, 2, 4, ..., 252, 254]的数据会被分散存储到目的操作数中。；index中的值必须唯一。若存在重复的index值，系统仅保留其中一个对应的数据，其余将被忽略。无法确定具体保留哪一个，因此必须确保index值不重复。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Scatter](../../../basic_api/memory_vector_compute/scatter_gather/scatter_isasi.md)（`same_topic`）：《AscScatter》明确“根据索引值index将源操作数src中的元素分散存储到目的操作数dst中。”；它与《Scatter》的“根据目的地址偏移张量将连续输入张量的元素分散到结果张量的指定位置。”在实际调用参数、数据流或结果校验上直接衔接。
- [ScatterDiscrete](../../../basic_api/reg_vector_compute/reg_data_store/scatter_discrete.md)（`same_topic`）：ScatterDiscrete 是 C++ Reg API 下依据唯一 index 将 RegTensor 分散写入 UB 的对应接口，包含相同的离散地址契约。
- [asc_scatter](asc_scatter_deprecated.md)（`same_topic`）：asc_scatter 与《AscScatter》的实质衔接是：废弃 asc_scatter 的现行 C/基础/Reg Scatter 是迁移路径；三张故障卡直接约束 indices 形状、重复地址归约和写冲突。
<!-- cannbot:related:end -->
