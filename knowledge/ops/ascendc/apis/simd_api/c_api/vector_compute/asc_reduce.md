---
type: API
title: AscReduce
description: 以内置固定模式对应的二进制或者用户自定义输入的数值对应的gather mask（数据收集的掩码），从源操作数中选取元素写入目的操作数中。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_reduce.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscReduce

以内置固定模式对应的二进制或者用户自定义输入的数值对应的gather mask（数据收集的掩码），从源操作数中选取元素写入目的操作数中。
函数原型：void asc_reduce(__ubuf__ uint16_t* dst, __ubuf__ uint16_t* src0, __ubuf__ uint16_t* src1, uint32_t count)
约束：接口不支持通过asc_set_vector_mask配置掩码。；dst、src0、src1的起始地址需要32字节对齐。；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscGetRsvdCount](asc_get_rsvd_count.md)（`related`）：《AscReduce》说明以内置固定模式对应的二进制或者用户自定义输入的数值对应的gather mask（数据收集的掩码），从源操作数中选取元素写入目的操作数中。；《AscGetRsvdCount》说明此接口用于获取执行asc_reduce操作后剩余的元素数量。。二者在AscReduce是按mask压缩选中元素的gather语义，GatherMask提供等价数据选择，AscGetRsvdCount读取实际保留数量上存在可执行的直接衔接。
- [GatherMask](../../basic_api/memory_vector_compute/compare_and_select/gather_mask.md)（`same_topic`）：《AscReduce》说明以内置固定模式对应的二进制或者用户自定义输入的数值对应的gather mask（数据收集的掩码），从源操作数中选取元素写入目的操作数中。；《GatherMask》说明以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。。二者在AscReduce是按mask压缩选中元素的gather语义，GatherMask提供等价数据选择，AscGetRsvdCount读取实际保留数量上存在可执行的直接衔接。
<!-- cannbot:related:end -->
