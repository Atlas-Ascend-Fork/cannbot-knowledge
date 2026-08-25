---
type: API
title: TBufPool
description: TBufPool接口索引页，包含简介、构造函数、InitBufPool、InitBuffer与Reset。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/TBufPool.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TBufPool

TBufPool 接口集合，用于管理 AscendC 片上 Buffer 池，支持多 TBuf 共享池内存。通过构造函数创建实例，InitBufPool/InitBuffer 初始化池与 buffer，Reset 重置池状态。相比单个 TBuf，TBufPool 在多 buffer 场景下可更高效利用内存，适用于需要多个临时 buffer 的算子。

<!-- cannbot:related:start -->
## 相关

- [InitBuffer](init_buffer.md)（`same_topic`）：TBufPool 类型页定义 InitBuffer 所操作的池对象和生命周期。
- [Reset](reset.md)（`same_topic`）：Reset 与《TBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TBufPool](t_buf_pool_constructor.md)（`same_topic`）：类型页定义构造函数产生的池对象和容量成员。
- [TBufPool简介](t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《TBufPool》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；TBufPool正文界定“TBufPool接口索引页，包含简介、构造函数、InitBufPool、InitBuffer与Reset”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
