---
type: API
title: SetSkipMsg
description: AIC跳过指定个数假消息的处理，仅在回调函数中调用。下图中Block0通过调用SetSkipMsg跳过三个假消息。 图1 SetSkipMsg示意图
  !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/SetSkipMsg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# SetSkipMsg

AIC 跳过指定个数的假消息处理，仅在回调函数中调用。配合 PostFakeMsg 实现消息合并机制。

原型：`__aicore__ inline void SetSkipMsg(uint8_t skipCnt)`。参数 skipCnt 为跳过的假消息个数。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [PostFakeMsg](post_fake_msg.md)（`related`）：AIV PostFakeMsg 通知后，AIC 通过 SetSkipMsg 跳过对应重复消息，构成发送与消费控制链。
<!-- cannbot:related:end -->
