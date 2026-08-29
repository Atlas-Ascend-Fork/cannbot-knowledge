---
type: API
title: ReduceDataBlock
description: 在每个DataBlock内根据ReduceType将数据归约为单一值，支持SUM、MAX和MIN三种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reduction_compute/ReduceDataBlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ReduceDataBlock

归约指令根据ReduceType，将数据集合在每个DataBlock（32B）内简化为单一值。

当ReduceType为SUM，将每个DataBlock（32B）中参与计算的元素相加，并将最终的计算结果依次保存在dstReg的最低位。

当ReduceType为MAX，将每个DataBlock（32B）中的最大值依次保存在dstReg中的最低位。

当ReduceType为MIN，将每个DataBlock（32B）中的最小值依次保存在dstReg中的最低位。

参数：type: ReduceType类型，支持SUM、MAX、MIN。 enum class ReduceType { SUM = 0, MAX, MIN, };；T: 目的操作数和源操作数的数据类型。；mode: MaskMergeMode，选择MERGING模式或ZEROING模式。当前仅支持ZEROING模式。 • ZEROING，mask未筛选的元素在dst中置零。 • MERGING，当前不支持。；U: 目的操作数和源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。；mask: 源操作数元素操作的有效指示，详细说明请参考MaskReg。

约束：- 对于归约求最大值，max(-0, +0) = +0。
- 对于归约求最小值，min(-0, +0) = -0。
- 对于归约求数据总和，mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行处理。
- 对于归约求最大值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最小值进行处理。
- 对于归约求最小值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最大值进行处理。
- mask为空场景及异常值处理参考mask为空场景及异常值处理。
- 指令内累加顺序采用二叉树累加方式，规则参考ReduceType::SUM累加顺序。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reduce](reduce.md)（`related`）：归约指令根据ReduceType，将数据集合简化为单一值或者更小的集合。；归约指令根据ReduceType，将数据集合在每个DataBlock（32B）内简化为单一值。。前者给出跨有效元素集合的通用 Reduce，后者把同一 ReduceType 约束到每个 32B DataBlock 内，能够在实现归约时依据目标范围选择全局式或块内式原语。
<!-- cannbot:related:end -->
