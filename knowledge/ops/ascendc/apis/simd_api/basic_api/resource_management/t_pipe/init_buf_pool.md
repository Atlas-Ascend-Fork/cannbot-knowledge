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

- [GetBaseAddr](get_base_addr.md)（`related`）：BufPool 绑定各 logicPos 的基址，是查询值来源。
- [InitBufPool](../t_buf_pool/init_buf_pool.md)（`related`）：TPipe::InitBufPool 先划出总资源池，TBufPool::InitBufPool 再从父池创建子池，构成明确的两级内存池初始化链。
- [InitBuffer](../t_buf_pool/init_buffer.md)（`related`）：创建 TBufPool 后，InitBuffer 才从该池为 TQue/TBuf 分配具体 buffer，直接承接资源池初始化。
- [InitBuffer](init_buffer.md)（`related`）：InitBuffer 负责“用于为TQue等队列和TBuf分配内存”；InitBufPool 负责“初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景”。
- [Reset](../t_buf_pool/reset.md)（`same_topic`）：Reset 与《InitBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《InitBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；InitBufPool正文界定“初始化TBufPool内存资源池，适用于内存资源有限时手动指定UB/L1内存资源复用的场景”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
