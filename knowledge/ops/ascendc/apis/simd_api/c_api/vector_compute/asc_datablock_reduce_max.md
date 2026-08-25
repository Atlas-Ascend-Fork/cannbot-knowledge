---
type: API
title: AscDatablockReduceMax
description: 执行数据块内的求最大值规约（Reduce Max）操作。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_datablock_reduce_max.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscDatablockReduceMax

执行数据块内的求最大值规约（Reduce Max）操作。
函数原型：void asc_datablock_reduce_max(__ubuf__ half* dst, __ubuf__ half* src, uint32_t count)
约束：操作数地址重叠约束请参考通用地址重叠约束。；dst、src的起始地址需要32字节对齐。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [AscDatablockReduceSum](asc_datablock_reduce_sum.md)（`related`）：AscDatablockReduceSum 与《AscDatablockReduceMax》的实质衔接是：AscDatablockReduceSum 与 max/min、Reg datablock、repeat 和基础 ReduceDataBlock 共享数据块归约契约；GetDataBlockSizeInBytes 决定一次数据块所覆盖的有效元素。
- [AscReduceMaxDatablock](../reg/reduce_compute/asc_reduce_max_datablock.md)（`related`）：两卡都对每个 32B DataBlock 求最大值；Memory C API 从 UB 输入，Reg API 在 mask 下把各块最大值连续写到 dst 低位并明确全 mask 块为 -inf。
- [AscReduceMax](../reg/reduce_compute/asc_reduce_max.md)（`same_topic`）：AscReduceMax 与《AscDatablockReduceMax》的实质衔接是：这些接口都是最大值归约的不同执行层或粒度；count 排除 padding 和跨 chunk 显式累加案例直接约束 AscReduceMax 的参与元素及分块合并方式。
<!-- cannbot:related:end -->
