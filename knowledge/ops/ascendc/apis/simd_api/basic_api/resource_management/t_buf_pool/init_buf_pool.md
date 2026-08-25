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

<!-- cannbot:related:start -->
## 相关

- [InitBufPool](../t_pipe/init_buf_pool.md)（`related`）：TPipe::InitBufPool 先划出总资源池，TBufPool::InitBufPool 再从父池创建子池，构成明确的两级内存池初始化链。
- [InitBuffer](init_buffer.md)（`same_topic`）：InitBufPool 初始化池的地址范围，InitBuffer 再从池中为具体 TBuf/TQue 分配块，两者是分层分配链。
- [Reset](reset.md)（`same_topic`）：Reset 与《InitBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TBufPool](t_buf_pool_constructor.md)（`same_topic`）：构造后需 InitBufPool 绑定物理范围才可分配。
- [TBufPool简介](t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《InitBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；InitBufPool正文界定“从Tpipe或TBufPool划分资源池，支持非共享模式和共享模式（复用已有资源池地址）”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
