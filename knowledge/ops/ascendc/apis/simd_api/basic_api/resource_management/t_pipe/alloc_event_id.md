---
type: API
title: AllocEventID
description: 用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/AllocEventID.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# AllocEventID

头文件路径为："basic_api/kernel_tpipe.h"。

用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。

约束：TEventID有数量限制，使用结束后应该立刻调用ReleaseEventID释放，防止TEventID耗尽。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 掩码向量化未修复 triu 大 shape 失败](../../../../../runbooks/performance/duplicate_triu_shape.md)（`exemplifies`）：《AllocEventID》明确“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。”；它与《Duplicate 掩码向量化未修复 triu 大 shape 失败》的“triu 大 shape Case9 失败初判为标量 SetValue 掩码瓶颈，改 Duplicate 0 填充向量化后仍失败；后续 timing 定位实为 per-tile event flag 耗尽的正确性问题（非超时），Duplicate 向量化路线 banned。”在实际调用参数、数据流或结果校验上直接衔接。
- [Destroy](destroy.md)（`related`）：显式分配的 event 必须在销毁前不再被使用。
- [ReleaseEventID](release_event_id.md)（`related`）：AllocEventID 占用的 HardEvent TEventID 必须由同一 TPipe 的 ReleaseEventID 释放；两接口构成不可缺失的资源生命周期。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag.md)（`related`）：SetFlag/WaitFlag 需要有效 TEventID；当事件需持有或同管线重复使用时应由 AllocEventID 分配并在生命周期末释放。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《AllocEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [FetchEventID](fetch_event_id.md)（`same_topic`）：FetchEventID 只临时取得静态事件号且不占用资源，重复同 pipeline 可能死锁；AllocEventID 则为需要持有或重复同管线同步的场景分配可管理 ID。
- [FreeAllEvent](../t_que_bind/free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《AllocEventID》明确“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
<!-- cannbot:related:end -->
