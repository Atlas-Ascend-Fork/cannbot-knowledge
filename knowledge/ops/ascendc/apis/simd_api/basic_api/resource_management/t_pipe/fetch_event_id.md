---
type: API
title: FetchEventID
description: 根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/FetchEventID.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# FetchEventID

头文件路径为："basic_api/kernel_tpipe.h"。

根据HardEvent（硬件类型的同步事件）获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。

约束：相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。在一些复杂的使用场景下，需要开发者自行保证使用正确。比如相同流水连续调用SetFlag/WaitFlag，如果两次传入的ID都是使用FetchEventID获取的，因为两者ID相同会出现程序卡死等未定义行为，这时推荐用户使用AllocEventID。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [GetTPipePtr 错加 AscendC 命名空间导致编译失败](../../../../../runbooks/compilation/gettpipeptr_is_global_function.md)（`exemplifies`）：GetTPipePtr 错加 AscendC 命名空间导致编译失败 与《FetchEventID》的实质衔接是：GetTPipePtr 是返回 AscendC::TPipe* 的全局函数；全局符号前缀案例和 FetchEventID/SetFlag/WaitFlag API共同说明只应去掉函数名上的 AscendC::。
- [ReleaseEventID](release_event_id.md)（`related`）：《FetchEventID》明确“根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”；它与《ReleaseEventID》的“用于释放HardEvent硬件同步事件的TEventID，通常与AllocEventID搭配使用。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag.md)（`related`）：FetchEventID 取得的 TEventID 作为 SetFlag/WaitFlag 的同步标识，后者是该临时 ID 的直接消费者。
- [AllocEventID](alloc_event_id.md)（`same_topic`）：FetchEventID 只临时取得静态事件号且不占用资源，重复同 pipeline 可能死锁；AllocEventID 则为需要持有或重复同管线同步的场景分配可管理 ID。
- [DestroyWithoutPipeAll](destroy_without_pipe_all.md)（`same_topic`）：DestroyWithoutPipeAll 与《FetchEventID》的实质衔接是：DestroyWithoutPipeAll 释放 TPipe 但不插入 PIPE_ALL，调用前需自行完成事件/流水同步；Destroy、EventID 释放和 TPipe 范式给出完整销毁顺序。
- [FreeAllEvent](../t_que_bind/free_all_event.md)（`same_topic`）：《FreeAllEvent》处理“释放TQueBind队列中申请的所有同步事件，便于在Buffer数量超过同步事件限制时重新申请队列。”。《FetchEventID》明确“根据HardEvent获取相应可用的TEventID，此接口不会申请TEventID，仅提供可用的TEventID。”，可直接用于核对FreeAllEvent 对 TQueBind 事件和 Alloc/Fetch/Release event ID 生命周期的回收合同。
<!-- cannbot:related:end -->
