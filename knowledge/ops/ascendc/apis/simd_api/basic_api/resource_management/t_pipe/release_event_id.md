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

- [AllocEventID](alloc_event_id.md)（`related`）：用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用该接口后，会占用申请的TEventID，直至调用ReleaseEventID释放。；约束：AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。。AllocEventID 产生并占用 TEventID，ReleaseEventID 消费该句柄并结束占用；申请与释放是同一资源生命周期中的相反步骤，而不是同一接口主题的模式变体。
- [FetchEventID](fetch_event_id.md)（`related`）：“相比于AllocEventID，FetchEventID适用于临时使用ID的场景，获取ID后，不会对ID进行占用。”说明 Fetch 路线没有释放生命周期；“AllocEventID、ReleaseEventID需成对出现，ReleaseEventID传入的TEventID需由对应的AllocEventID申请而来。”界定改用独占 ID 后必须履行的释放合同。
<!-- cannbot:related:end -->
