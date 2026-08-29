---
type: API
title: InitBuffer
description: 为TQue或TBuf进行内存分配，支持指定内存块个数和大小。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/InitBuffer.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBuffer

头文件路径为："basic_api/kernel_tpipe.h"。

调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配。

参数：T: que参数的类型。；pos: Buffer逻辑位置，可以为VECIN、VECOUT、VECCALC、A1、B1、C1。关于TPosition的具体介绍请参考TPosition。

约束：声明TBufPool时，可以通过bufIDSize指定可分配Buffer的最大数量，默认上限为4，最大为16。TQue或TBuf的物理内存需要和TBufPool一致。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [InitBufPool](init_buf_pool.md)（`related`）：调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配；整块TbufPool资源可以继续通过TBufPool::InitBufPool接口划分成小块资源；先划分子池再从子池为队列或临时缓冲分配内存，构成同一资源生命周期的相邻步骤。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`related`）：TBufPool::InitBuffer接口分配Buffer；调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配。。焦点接口先从整体内存划分子资源池，候选接口再从该 TBufPool 向 TQue/TBuf 分配具体 Buffer。
<!-- cannbot:related:end -->
