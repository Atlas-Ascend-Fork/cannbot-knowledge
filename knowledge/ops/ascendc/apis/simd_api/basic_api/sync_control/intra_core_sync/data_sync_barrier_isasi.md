---
type: API
title: DataSyncBarrier
description: 阻塞后续指令执行，直到所有之前的内存访问指令执行结束，可通过模板参数控制需要等待的内存位置，用于解决Scalar的内存依赖。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/DataSyncBarrier_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# DataSyncBarrier

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束，用于解决Scalar的内存依赖。

参数：arg0: 模板参数，表示需要等待的内存位置，类型为MemDsbT，可取值为： &bull; ALL，等待GM和UB的访问指令（不包括其他内存位置，例如L0C Buf。

约束：等待的内存位置取值为ALL时，只能等待GM和UB的访问指令，不包括其他内存位置，例如L0C Buffer、L1 Buffer。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品 支持。

<!-- cannbot:related:start -->
## 相关

- [DepthwiseConv2D 950 Direct Invoke 算子知识](../../../../../operators/direct/nn/conv/depthwise_conv_2d_950.md)（`related`）：“｜ index ｜ `DataSyncBarrier<UB>` ｜ scalar writes ｜ VF ｜ index table ｜ exact uint32 index ｜”；“阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束，用于解决Scalar的内存依赖。”。stride-2 Gather route 在 Scalar 写 index table 后用 UB barrier 再让 VF 读取，API 合同解释该依赖为何必要。
- [GatherNd 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/index/gather_nd_950.md)（`related`）：shape helper ｜ `DataSyncBarrier<UB>` ｜ scalar SetValue ｜ SIMD ｜ helpTBuf ｜ T3 int32/64 exact阻塞后续的指令执行，直到所有之前的内存访问指令（需要等待的内存位置可通过参数控制）执行结束，用于解决Scalar的内存依赖。GatherNd 的 shape helper 表明确实由 Scalar 写 `helpTBuf`、随后交给 SIMD 消费，接口卡定义屏障等待先前内存访问完成；在该位置插入 UB 屏障正好闭合生产者到消费者的数据依赖。
<!-- cannbot:related:end -->
