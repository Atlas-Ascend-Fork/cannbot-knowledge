---
type: API
title: Reduce
description: 根据ReduceType将数据集合归约为单一值或更小集合，支持SUM求和、MAX最大值和MIN最小值三种模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reduction_compute/Reduce.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Reduce

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_reduce_intf.h"。

归约指令根据ReduceType，将数据集合简化为单一值或者更小的集合。

ReduceType::SUM：根据mask，计算源操作数srcReg内有效元素的数据总和，将结果写入目的操作数dstReg。

ReduceType::MAX：根据mask，计算源操作数srcReg内有效元素中的最大值和索引，将结果写入目的操作数dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中。

ReduceType::MIN：根据mask，计算源操作数srcReg内有效元素中的最小值和索引，将结果写入目的操作数dstReg，当存在多个最小值时，会将第一个最小值的索引保存在dstReg中。

参数：type: ReduceType类型，支持SUM、MAX、MIN。 enum class ReduceType { SUM = 0, MAX, MIN, };；T: 目的操作数dstReg的数据类型。；U: 源操作数srcReg的数据类型。；mode: MaskMergeMode，选择MERGING模式或ZEROING模式。 • ZEROING，mask未选中的元素在dst中置零。 • MERGING，当前不支持。；S: 目的操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；V: 源操作数的RegTensor类型，例如RegTensor ，由编译器自动推导，用户不需要填写。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。

约束：- 对于归约求数据总和，mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行处理。
- 对于归约求最大值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最小值进行处理。
- 对于归约求最小值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最大值进行处理。
- 对于归约求最大值，当所有元素均不参与计算时，将该数据类型的最小值写入dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中，max(-0, +0) = +0。
- 对于归约求最小值，当所有元素均不参与计算时，将该数据类型的最大值写入dstReg，当存在多个最小值时，会将第一个最小值的索引保存在dstReg中，min(-0, +0) = -0。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Reduce count 必须排除 DMA 对齐填充元素](../../../../../runbooks/precision/reduction_count_excludes_dma_padding.md)（`exemplifies`）：Reduce count 必须排除 DMA 对齐填充元素 与《Reduce》的实质衔接是：DMA 对齐容量不是 Reduce 的数学 count；DataCopyPad/padding 故障、Softmax 与 ReduceMax/Sum 各层入口共同验证填充零经 Exp 后会污染分母。
- [int32 fp32累加reduce binary_equal不可达](../../../../../runbooks/precision/int32_fp32_reduce_binary_equal.md)（`exemplifies`）：《int32 fp32累加reduce binary_equal不可达》的任务是“int32 输入的 reduce 类算子内部 cast 到 fp32 累加，kernel 的 ReduceSum+bisection cache tree 与 golden 的 pairwise 折半是两棵不同 reduce 树；sum 超过 fp32 精确整数范围 2^24 时舍入路径不同致 1 ULP 差，cast 回 int32 后 bitwise 不一致，binary_equal 永不可达。”。《Reduce》具体提供“根据ReduceType将数据集合归约为单一值或更小集合，支持SUM求和、MAX最大值和MIN最小值三种模式。”，它直接用于int32→fp32 ReduceSum 的规约树、有效 count 和 2^24 舍入边界。
- [ReduceDataBlock](reduce_data_block.md)（`related`）：ReduceDataBlock 只产生每块的局部结果，Reg::Reduce 可继续把数据集合归并为单值或更小集合，构成分层归约链。
- [ReduceMax](../../memory_vector_compute/reduction_compute/reduce_max.md)（`related`）：Reg::Reduce 的 MAX 与 ReduceMax 都完成最大值归约，但分别面向寄存器编程和 LocalTensor 内存向量接口。
- [ReduceMin](../../memory_vector_compute/reduction_compute/reduce_min.md)（`related`）：Reg::Reduce 的 MIN 与 ReduceMin 都完成最小值归约，但分别面向寄存器编程和 LocalTensor 内存向量接口。
- [ReduceSum](../../memory_vector_compute/reduction_compute/reduce_sum.md)（`related`）：Reg::Reduce 的 SUM 与 ReduceSum 都完成向量求和归约，但分别面向寄存器编程和 LocalTensor 内存向量接口。
<!-- cannbot:related:end -->
