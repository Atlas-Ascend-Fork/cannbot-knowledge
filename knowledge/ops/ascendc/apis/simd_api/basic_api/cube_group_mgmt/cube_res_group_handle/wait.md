---
type: API
title: Cube核间管理Wait
description: 在调用PostMessage或PostFakeMessage后，查询该消息是否已被AIC处理完。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/Wait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# Cube核间管理Wait

调用 PostMessage 或 PostFakeMsg 后，查询消息是否已被 AIC 处理完。

原型：`template <bool sync = true> __aicore__ inline bool Wait(uint16_t offset)`。参数 offset 为 PostMessage/PostFakeMsg 返回的偏移量。模板 sync=true 时阻塞等待，false 时非阻塞查询。返回 true 表示已处理完。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《Cube核间管理Wait》明确“在调用PostMessage或PostFakeMessage后，查询该消息是否已被AIC处理完。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CubeResGroupHandle](cube_res_group_handle_usage.md)（`related`）：PostMessage 后 AIV 必须用 Wait 等待 AIC 把消息状态推进到 DONE，才能安全回收或继续。
- [FreeMessage](free_message.md)（`related`）：Wait 确认消息处理后仍需 FreeMessage 归还消息资源，否则同步槽生命周期不闭合。
- [PostFakeMsg](post_fake_msg.md)（`related`）：PostFakeMsg 提供无需真实任务消息时仍可满足 Wait 协议的生产端，与 Wait 的 offset 契约直接配套。
- [PostMessage](post_message.md)（`related`）：PostMessage 返回的 offset 专供 Wait 查询 AIC 是否处理完成，二者形成发送与完成确认协议。
- [SetQuit](set_quit.md)（`same_topic`）：SetQuit 与《Cube核间管理Wait》的实质衔接是：SetQuit 是 CubeResGroupHandle 消息循环的退出信号，usage 与 Wait 解释信号写入后的消费和收尾。
<!-- cannbot:related:end -->
