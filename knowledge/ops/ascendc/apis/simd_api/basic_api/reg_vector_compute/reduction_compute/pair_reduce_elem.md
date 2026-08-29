---
type: API
title: PairReduceElem
description: 将源寄存器中相邻两个数值相加，结果保存在目的寄存器的低位位置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reduction_compute/PairReduceElem.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# PairReduceElem

头文件路径为："basic_api/kernel_operator_vec_reduce_intf.h"。

将传入的srcReg中相邻两个数值相加，并将产生的结果保存在dstReg中的低位位置。

参数：type: 具体的PairReduce类型，当前仅支持归约求和计算。 enum class PairReduce { SUM = 0, };；T: 目的操作数和源操作数的数据类型。；mode: MaskMergeMode，选择MERGING模式或ZEROING模式。 • ZEROING，mask未筛选的元素在dst中置零。目前仅支持该模式。 • MERGING，当前不支持。；U: 目的操作数和源操作数的RegTensor类型，由编译器自动推导，用户不需要填写。；dstReg: 目的操作数。 类型为RegTensor。；srcReg: 源操作数。 类型为RegTensor。；mask: 源操作数元素操作的有效指示，详细说明请参考MaskReg。

支持数据类型：half、float。

约束：- mask指定源操作数是否参与计算，不参与计算的元素，被当作0进行累加。例如
  - 若连续两个元素a、b均不参与计算，目的操作数结果为0。
  - 若连续两个元素a、b仅元素a参与计算，目的操作数结果为a。
  - 若连续两个元素a、b仅元素b参与计算，目的操作数结果为b。

- 求和后，dst中仅前一半元素为有效数据，后一半填充为0。搬出至UB时需要避免数据踩踏。

仅 Ascend 950PR/Ascend 950DT 支持。
