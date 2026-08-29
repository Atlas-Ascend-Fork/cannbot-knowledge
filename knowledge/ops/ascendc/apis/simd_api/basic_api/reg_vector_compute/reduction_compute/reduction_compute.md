---
type: API
title: 归约计算
description: Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reduction_compute/reduction_compute.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950']
---

# 归约计算

Reg矢量计算归约接口索引页，包含Reduce、ReduceDataBlock与PairReduceElem。

归约指令根据ReduceType，将数据集合简化为单一值或者更小的集合。 ReduceType::SUM：根据mask，计算源操作数srcReg内有效元素的数据总和，将结果写入目的操作数dstReg。 ReduceType::MAX：根据mask，计算源操作数srcReg内有效元素中的最大值和索引，将结果写入目的操作数dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中。 ReduceType::MIN：根据mask，计算源操作数srcReg内有效元素中的最小值和索引，将结果写入目的操作数dstReg，当存在多个最小值时，会将第一个最小值的索引保存在dstReg中。

本接口组包含 Reduce, ReduceDataBlock, PairReduceElem。

本接口属于 Reg 矢量计算归约接口，对 RegTensor 数据进行归约运算。

约束：对于归约求数据总和，mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行处理。；对于归约求最大值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最小值进行处理。；对于归约求最小值，mask指定源操作数是否参与计算，不参与计算的元素，被当作数据类型的最大值进行处理。；对于归约求最大值，当所有元素均不参与计算时，将该数据类型的最小值写入dstReg，当存在多个最大值时，会将第一个最大值的索引保存在dstReg中，max(-0, +0) = +0。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
