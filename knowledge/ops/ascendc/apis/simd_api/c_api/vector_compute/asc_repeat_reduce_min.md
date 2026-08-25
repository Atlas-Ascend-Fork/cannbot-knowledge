---
type: API
title: AscRepeatReduceMin
description: 对每个 Repeat 的元素求最小值，并返回首个最小值在该 Repeat 中的索引；一次 Repeat 处理 256 字节。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_repeat_reduce_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: [a2, a3]
---


# AscRepeatReduceMin

对每个Repeat内所有元素求最小值，以及Repeat内的首个最小值元素在当前Repeat中的索引index。一次Repeat计算256字节。 index_value接口：表示index位于低半部，返回结果存储顺序为[index, value]。输入数据类型为half时，index数据类型为uint16；输入数据类型为float时，index数据类型为uint32。 value_index接口：表示value位于低半部，返回结果存储顺序为[value, index]。输入数据类型为half时，index数据类型为uint16；输入数据类型为float时，index数据类型为uint32。
函数原型：void asc_repeat_reduce_min_index_value(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：输出中的索引index的数据是按照dst的数据类型进行存储，比如float输出的index数据应该为uint32，则读取时需要将float重新解释为uint32。；操作数地址重叠约束请参考通用地址重叠约束。；dst的起始地址，输入类型为half时需要4字节对齐，输入类型为float时需要8字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceMin](asc_datablock_reduce_min.md)（`related`）：RepeatReduceMin 跨多个 repeat 继续归约，而 DataBlockReduceMin 只处理块粒度，输出需求决定选型。
- [AscRepeatReduceMax](asc_repeat_reduce_max.md)（`related`）：RepeatReduceMin 与 RepeatReduceMax 具有相同 repeat、值/索引布局和搬运契约，只切换极值方向。
- [AscRepeatReduceSum](asc_repeat_reduce_sum.md)（`related`）：AscRepeatReduceMin 与 Sum 共享每 Repeat 独立归约的执行粒度，Min 则返回首个最小值索引。
- [ReduceRepeat](../../basic_api/memory_vector_compute/reduction_compute/reduce_repeat.md)（`related`）：C++ ReduceRepeat 是同类重复规约的基础 API，补充 mask 和 repeat 语义，可与 C API 签名相互映射。
- [AscGetReduceMinCnt](asc_get_reduce_min_cnt.md)（`same_topic`）：AscGetReduceMinCnt 在同步后取回 RepeatReduceMin 产生的最小值和索引，是结果消费链的直接下一步。
- [AscReduceMinDatablock](../reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscRepeatReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《AscRepeatReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
