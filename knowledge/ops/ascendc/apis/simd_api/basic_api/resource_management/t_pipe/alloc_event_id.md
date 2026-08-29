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

- [FetchEventID](fetch_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”给出不占用路线；“用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。”给出复杂同步需要独占 ID 时的替代生命周期。
- [ReleaseEventID](release_event_id.md)（`related`）：用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。；约束：AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。。AllocEventID 产生并占用 TEventID，ReleaseEventID 消费该句柄并结束占用；申请与释放是同一资源生命周期中的相反步骤，而不是同一接口主题的模式变体。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag.md)（`related`）：参数：id(输入): 事件ID，由用户自己指定，推荐通过AllocEventID或者FetchEventID来获取。定义如下： using TEventID = int8_t;。；用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。。SetFlag/WaitFlag 消费 TEventID，AllocEventID 提供受生命周期管理的硬件事件 ID，闭合同步事件获取与使用。
- [SetFlag/WaitFlag](../../sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`related`）：- 在采用TPipe-TQue框架编程范式时，eventID需要通过AllocEventID或者FetchEventID来获取。；用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。。同步卡要求从 TPipe 获取 eventID，AllocEventID 提供带申请和释放生命周期的 HardEvent ID。
<!-- cannbot:related:end -->
