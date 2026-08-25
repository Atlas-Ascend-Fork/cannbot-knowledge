---
type: API
title: AscDatablockReduceMin
description: 执行数据块内的求最小值规约（Reduce Min）操作。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_datablock_reduce_min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscDatablockReduceMin

执行数据块内的求最小值规约（Reduce Min）操作。
函数原型：void asc_datablock_reduce_min(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceSum](asc_datablock_reduce_sum.md)（`related`）：AscDatablockReduceSum 与《AscDatablockReduceMin》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscGetReduceMinCnt](asc_get_reduce_min_cnt.md)（`related`）：GetReduceMinCnt 提供归约计数/辅助信息，和 DataBlockReduceMin 的最小值结果用途不同。
- [AscRepeatReduceMin](asc_repeat_reduce_min.md)（`related`）：RepeatReduceMin 跨多个 repeat 继续归约，而 DataBlockReduceMin 只处理块粒度，输出需求决定选型。
- [ReduceMin](../../adv_api/reduction_operations/reduce_min_interface/reduce_min.md)（`related`）：高阶 ReduceMin 封装 shape 与 workspace，适合整 tensor 归约；本接口适合显式 DataBlock 编程。
- [AscReduceMinDatablock](../reg/reduce_compute/asc_reduce_min_datablock.md)（`same_topic`）：AscReduceMinDatablock 与《AscDatablockReduceMin》的实质衔接是：AscReduceMinDatablock 在每个 DataBlock 取最小值；Reg/vector/basic 的 datablock 归约、repeat 归约及 block 大小查询共同决定输入粒度与结果位置。
- [ReduceMin](../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`same_topic`）：ReduceMin 与《AscDatablockReduceMin》的实质衔接是：ReduceMin 的高阶、基础、Reg 和 C 入口共享最小值归约，但索引、datablock/repeat 粒度及临时空间不同；A5 错例和使用指南直接限定选择与验证。
<!-- cannbot:related:end -->
