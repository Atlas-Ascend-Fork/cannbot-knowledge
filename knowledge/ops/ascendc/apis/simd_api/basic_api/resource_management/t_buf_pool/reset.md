---
type: API
title: Reset
description: 切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TBufPool/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

在切换TBufPool资源池时使用，结束当前TbufPool资源池正在处理的相关事件。调用后当前资源池及资源池分配的Buffer仍然存在，只是Buffer内容可能会被改写。可以切换回该资源池后，重新开始使用该Buffer，无需再次分配。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Destroy](../t_pipe/destroy.md)（`related`）：Reset 与《Destroy》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [DestroyWithoutPipeAll](../t_pipe/destroy_without_pipe_all.md)（`related`）：Reset 与《DestroyWithoutPipeAll》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [Reset](../custom_t_buf_pool/reset.md)（`related`）：“Reset”定义：完成自定义TBufPool资源的释放与eventId等变量的复位，调用后对应资源池及已分配Buffer不可继续使用。；“Reset”定义：切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在。。实质衔接：Custom pool Reset 会释放资源并使 Buffer 失效，必须与 Init 生命周期配对；普通 TBufPool.Reset 只切换事件且资源仍在，差异直接影响后续可用性。
- [Init](../custom_t_buf_pool/init.md)（`same_topic`）：Reset 与《Init》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [InitBufPool](init_buf_pool.md)（`same_topic`）：Reset 与《InitBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [InitBufPool](../t_pipe/init_buf_pool.md)（`same_topic`）：Reset 与《InitBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TBufPool](t_buf_pool.md)（`same_topic`）：Reset 与《TBufPool》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [TBufPool简介](t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《Reset》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [自定义TBufPool](../custom_t_buf_pool/custom_t_buf_pool.md)（`same_topic`）：焦点处理自定义 TBufPool 与基础 TBufPool 的资源池关系；Reset正文界定“切换TBufPool资源池时使用，结束当前资源池相关事件，资源池及Buffer仍然存在”。候选说明自定义 pool 如何建立在 TBufPool 的 InitBufPool/InitBuffer/Reset 生命周期上。
<!-- cannbot:related:end -->
