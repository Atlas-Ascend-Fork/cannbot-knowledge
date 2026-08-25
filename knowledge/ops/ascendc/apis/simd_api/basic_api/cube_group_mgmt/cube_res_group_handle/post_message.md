---
type: API
title: PostMessage
description: 通过AllocMessage接口获取到消息空间地址msg后，构造消息结构体CubeMsgType，发送该消息。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/PostMessage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# PostMessage

通过 AllocMessage 获取消息空间地址后，构造 CubeMsgType 消息结构体并发送。

原型：`template <PipeMode pipeMode = SCALAR_MODE> __aicore__ inline uint16_t PostMessage(__gm__ CubeMsgType* msg, CubeMsgType& msgInput)`。参数 msg 为目标消息空间地址，msgInput 为待发送消息内容。返回 uint16_t offset 用于后续 Wait 查询。模板 pipeMode 默认 SCALAR_MODE。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：PostMessage 的 msg 地址必须先由 AllocMessage 从深度为 4 的队列取得；这是发送前不可省略的资源分配步骤。
- [AssignQueue](assign_queue.md)（`related`）：AssignQueue 选定 AIV 对应队列，随后 PostMessage 将 AllocMessage 填好的消息沿该队列发送给 AIC。
- [CubeResGroupHandle](cube_res_group_handle_usage.md)（`related`）：AIV 在 AllocMessage 填好 CubeMsgType 后通过 PostMessage 提交给 AIC 回调，是 usage 中任务分发的核心交接点。
- [Cube核间管理Wait](wait.md)（`related`）：PostMessage 返回的 offset 专供 Wait 查询 AIC 是否处理完成，二者形成发送与完成确认协议。
- [FreeMessage](free_message.md)（`same_topic`）：FreeMessage 与《PostMessage》的实质衔接是：FreeMessage 释放由 AllocMessage 取得并经 PostMessage 流转的消息，CubeResGroupHandle 使用说明给出完整状态生命周期。
<!-- cannbot:related:end -->
