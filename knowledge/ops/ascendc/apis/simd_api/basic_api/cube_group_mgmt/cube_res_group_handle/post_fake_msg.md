---
type: API
title: PostFakeMsg
description: 在消息合并场景中由AIV发送假消息，通知AIC跳过重复消息的读取和处理，实现消息合并机制。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/PostFakeMsg.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# PostFakeMsg

在消息合并场景中由 AIV 发送假消息，通知 AIC 跳过重复消息的读取和处理。需先通过 AllocMessage 获取消息空间地址。

原型：`template <PipeMode pipeMode = SCALAR_MODE> __aicore__ inline uint16_t PostFakeMsg(__gm__ CubeMsgType* msg)`。参数 msg 为消息空间地址，返回 uint16_t offset。AIC 侧通过 SetSkipMsg 跳过对应数量的假消息。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [Cube核间管理Wait](wait.md)（`related`）：PostFakeMsg 提供无需真实任务消息时仍可满足 Wait 协议的生产端，与 Wait 的 offset 契约直接配套。
- [SetSkipMsg](set_skip_msg.md)（`related`）：AIV PostFakeMsg 通知后，AIC 通过 SetSkipMsg 跳过对应重复消息，构成发送与消费控制链。
<!-- cannbot:related:end -->
