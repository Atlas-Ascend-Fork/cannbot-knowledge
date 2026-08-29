---
type: API
title: AscRepeatReduceMax
description: 对每个 Repeat 的元素求最大值，并返回首个最大值在该 Repeat 中的索引；一次 Repeat 处理 256 字节。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_repeat_reduce_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscRepeatReduceMax

对每个Repeat内所有元素求最大值，以及Repeat内的首个最大值元素在当前Repeat中的索引index。一次Repeat计算256字节。 index_value接口：表示index位于低半部，返回结果存储顺序为[index, value]。输入数据类型为half时，index数据类型为uint16；输入数据类型为float时，index数据类型为uint32。 value_index接口：表示value位于低半部，返回结果存储顺序为[value, index]。输入数据类型为half时，index数据类型为uint16；输入数据类型为float时，index数据类型为uint32。
函数原型：void asc_repeat_reduce_max_index_value(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：输出中的索引index的数据是按照dst的数据类型进行存储，比如float输出的index数据应该为uint32，则读取时需要将float重新解释为uint32。；操作数地址重叠约束请参考通用地址重叠约束。；dst的起始地址，输入类型为half时需要4字节对齐，输入类型为float时需要8字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscGetReduceMaxCnt](asc_get_reduce_max_cnt.md)（`related`）：此接口用于获取执行asc_repeat_reduce_max操作后的最大值，以及第一个最大值时的索引。；对每个Repeat内所有元素求最大值，以及Repeat内的首个最大值元素在当前Repeat中的索引index。一次Repeat计算256字节。。GetReduceMaxCnt 明确读取 AscRepeatReduceMax 的执行结果，目标接口定义每个 Repeat 产生的最大值与首个索引，因此二者构成先归约、再提取结果的调用链。
<!-- cannbot:related:end -->
