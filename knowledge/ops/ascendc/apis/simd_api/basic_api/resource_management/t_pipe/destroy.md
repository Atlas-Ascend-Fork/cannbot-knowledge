---
type: API
title: Destroy
description: 释放TPipe资源，用于重复申请释放TPipe，创建TPipe对象后可调用Destroy手动释放资源。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Destroy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Destroy

头文件路径为："basic_api/kernel_tpipe.h"。

释放资源。

约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocEventID](alloc_event_id.md)（`related`）：显式分配的 event 必须在销毁前不再被使用。
- [Init](init.md)（`related`）：TPipe Init 建立资源状态，Destroy 释放同一对象的资源；重复复用 TPipe 时二者构成明确的初始化/清理生命周期。
- [Reset](../t_buf_pool/reset.md)（`related`）：Reset 与《Destroy》的实质衔接是：Reset 结束当前 TBufPool 事件但保留 pool/buffer，必须放在 InitBufPool/Init 与 Destroy 之间；自定义池说明给出切换资源池的生命周期。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《Destroy》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [TBufPool简介](../t_buf_pool/t_buf_pool_intro.md)（`same_topic`）：TBufPool简介 与《Destroy》的实质衔接是：TBufPool 在 TPipe 下手工复用 UB/L1，必须依次 InitBufPool、分配/取址、Reset 或 Destroy；所连容量和 TPipe 初始化案例直接约束资源预算与生命周期。
- [TPipe](t_pipe.md)（`same_topic`）：类型页定义 Destroy 释放的 event 和 buffer pool 生命周期。
<!-- cannbot:related:end -->
