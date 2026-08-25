---
type: API
title: ReleaseEventID
description: 用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/ReleaseEventID.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# ReleaseEventID

头文件路径为："basic_api/kernel_tpipe.h"。

用于释放HardEvent（硬件类型同步事件）的TEventID，通常与AllocEventID搭配使用。

约束：AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 掩码向量化未修复 triu 大 shape 失败](../../../../../runbooks/performance/duplicate_triu_shape.md)（`exemplifies`）：《ReleaseEventID》明确“用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。”；它与《Duplicate 掩码向量化未修复 triu 大 shape 失败》的“triu 大 shape Case9 失败初判为标量 SetValue 掩码瓶颈，改 Duplicate 0 填充向量化后仍失败；后续 timing 定位实为 per-tile event flag 耗尽的正确性问题（非超时），Duplicate 向量化路线 banned。”在实际调用参数、数据流或结果校验上直接衔接。
- [AllocEventID](alloc_event_id.md)（`related`）：AllocEventID 占用的 HardEvent TEventID 必须由同一 TPipe 的 ReleaseEventID 释放；两接口构成不可缺失的资源生命周期。
- [FetchEventID](fetch_event_id.md)（`related`）：《FetchEventID》明确“根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”；它与《ReleaseEventID》的“用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。”在实际调用参数、数据流或结果校验上直接衔接。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《ReleaseEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [FreeAllEvent](../t_que_bind/free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《ReleaseEventID》明确“用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
<!-- cannbot:related:end -->
