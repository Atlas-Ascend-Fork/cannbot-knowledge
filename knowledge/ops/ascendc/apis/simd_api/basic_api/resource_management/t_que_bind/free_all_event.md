---
type: API
title: FreeAllEvent
description: 释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/FreeAllEvent.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# FreeAllEvent

头文件路径为："basic_api/kernel_tpipe.h"。

释放队列中申请的所有同步事件。队列分配的Buffer关联着同步事件的eventID，因为同步事件的数量有限制，如果同时使用的队列Buffer数量超过限制，将无法继续申请队列，使用本接口释放队列中的事件后，可以再次申请队列。详细介绍

约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocEventID](../t_pipe/alloc_event_id.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《AllocEventID》明确“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [DestroyWithoutPipeAll](../t_pipe/destroy_without_pipe_all.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《DestroyWithoutPipeAll》明确“释放TPipe资源，用于重复申请释放TPipe。内部未设置PIPE_ALL同步，需开发者自行保证同步流水正确。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [FetchEventID](../t_pipe/fetch_event_id.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《FetchEventID》明确“根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [ReleaseEventID](../t_pipe/release_event_id.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《ReleaseEventID》明确“用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [TQueBind](t_que_bind.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind》明确“TQueBind接口索引页，包含简介、构造函数、AllocTensor/FreeTensor、EnQue/DeQue及BufHandle管理。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [TQueBind](t_que_bind_constructor.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind》明确“TQueBind构造函数，用于创建TQueBind对象。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
- [TQueBind简介](t_que_bind_intro.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《TQueBind简介》明确“TQueBind绑定源逻辑位置和目的逻辑位置，根据源位置和目的位置，来确定内存分配的位置 、插入对应的同步事件，帮助开发者解决内存分配和管理、同步等问题。Tque是TQueBind的简化模式。通常情况下开发者使用TQue进行编程，TQueBind对外提供一些特殊数据通路的内存管理和同步控制，涉及这些通路时可以直接使用TQueBind。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
<!-- cannbot:related:end -->
