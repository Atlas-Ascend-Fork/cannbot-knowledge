---
type: API
title: InitBufPool
description: 从Tpipe或TBufPool划分资源池，支持非共享模式和共享模式（复用已有资源池地址）。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/InitBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBufPool

头文件路径为："basic_api/kernel_tpipe.h"。

通过Tpipe::InitBufPool接口可划分出整块资源，整块TbufPool资源可以继续通过TBufPool::InitBufPool接口划分成小块资源。

资源分配的非共享模式与共享模式
- 非共享模式：从Tpipe中划分出一块新的资源池。
- 共享模式：从Tpipe划分出的新资源池与其他资源池共享起始地址及长度。

约束：- 新划分的资源池与被复用资源池的物理内存需要一致，两者共享起始地址及长度；
- 输入长度需要小于等于被复用资源池长度；
- 其他泛用约束参考TBufPool；

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。
