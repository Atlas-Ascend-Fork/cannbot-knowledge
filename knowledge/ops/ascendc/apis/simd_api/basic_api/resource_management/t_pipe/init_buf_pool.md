---
type: API
title: InitBufPool
description: 初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/InitBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# InitBufPool

头文件路径为："basic_api/kernel_tpipe.h"。

初始化TBufPool内存资源池。本接口适用于内存资源有限时，希望手动指定UB/L1内存资源复用的场景。本接口初始化后在整体内存资源中划分出一块子资源池。划分出的子资源池TBufPool，提供了如下方式进行资源管理
-   TPipe::InitBufPool的重载接口指定与其他TBufPool子资源池复用;
-   TBufPool::InitBufPool接口对子资源池继续划分；
-   TBufPool::InitBuffer接口分配Buffer；

关于TBufPool的具体介绍及资源划分图示

约束：-   新划分的资源池与被复用资源池的硬件属性需要一致，两者共享起始地址及长度；
-   输入长度需要小于等于被复用资源池长度；
-   其他泛用约束参考TBufPool。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [ExternImplBufpool](../custom_t_buf_pool/extern_impl_bufpool.md)（`related`）：焦点卡规定“自定义TBufPool之前，必须通过TPipe::InitBufPool接口进行TBufPool内存资源池初始化”，候选卡说明初始化后“在整体内存资源中划分出一块子资源池”；该调用是使用自定义宏前不可省略的资源准备步骤。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：TBufPool::InitBuffer接口分配Buffer；调用TBufPool::InitBuffer接口为TQue/TBuf进行内存分配。。焦点接口先从整体内存划分子资源池，候选接口再从该 TBufPool 向 TQue/TBuf 分配具体 Buffer。
<!-- cannbot:related:end -->
