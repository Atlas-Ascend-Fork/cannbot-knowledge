---
type: API
title: SetFlag/WaitFlag
description: 同一核内不同流水线之间的同步指令，SetFlag设置硬件标志位，WaitFlag等待并清除标志位，用于具有数据依赖的不同流水指令间同步。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/SetFlag-WaitFlag.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetFlag/WaitFlag

头文件路径为："basic_api/kernel_operator_block_sync_intf.h"。

同一核内不同流水线之间的同步指令，具有数据依赖的不同流水指令之间需要插入此同步。

- SetFlag：当前序指令的所有读写操作都完成之后，当前指令开始执行，并将硬件中的对应标志位设置为1。
- WaitFlag：当执行到该指令时，如果发现对应标志位为0，该队列的后续指令将一直被阻塞；如果发现对应标志位为1，则将对应标志位设置为0，同时后续指令开始执行。

参数：id(输入): 事件ID，由用户自己指定，推荐通过AllocEventID或者FetchEventID来获取。定义如下： using TEventID = int8_t;。

约束：SetFlag/WaitFlag必须成对出现。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AllocEventID](../../resource_management/t_pipe/alloc_event_id.md)（`related`）：参数：id(输入): 事件ID，由用户自己指定，推荐通过AllocEventID或者FetchEventID来获取。定义如下： using TEventID = int8_t;。；用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。。SetFlag/WaitFlag 消费 TEventID，AllocEventID 提供受生命周期管理的硬件事件 ID，闭合同步事件获取与使用。
- [SetFlag/WaitFlag](set_flag_wait_flag_isasi.md)（`same_topic`）：如图1所示，SetFlag/WaitFlag接口用于核内多流水间的同步；同一核内不同流水线之间的同步指令，具有数据依赖的不同流水指令之间需要插入此同步。。两卡描述同一 SetFlag/WaitFlag 核内跨流水同步合同，ISASI 卡是该接口的平台版本。
<!-- cannbot:related:end -->
