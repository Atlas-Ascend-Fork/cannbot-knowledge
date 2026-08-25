---
type: API
title: SetQuit
description: 通过AllocMessage接口获取到消息空间地址后，发送退出消息，告知该消息队列对应的AIC无需处理该队列的消息。如下图，Queue5对应的AIV发了退出消息后，Block1将不再处理Queue5的任何消息。
  图1 消息队列退出示意图 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/SetQuit.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# SetQuit

通过 AllocMessage 获取消息空间地址后，发送退出消息，告知对应 AIC 无需再处理该队列的消息。

原型：`__aicore__ inline void SetQuit(__gm__ CubeMsgType* msg)`。参数 msg 为消息空间地址。发送后该消息队列对应的 AIC Block 将不再处理该队列的任何消息。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《SetQuit》明确“通过AllocMessage接口获取到消息空间地址后，发送退出消息，告知该消息队列对应的AIC无需处理该队列的消息。如下图，Queue5对应的AIV发了退出消息后，Block1将不再处理Queue5的任何消息。 图1 消息队列退出示意图”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CubeResGroupHandle](cube_res_group_handle.md)（`same_topic`）：SetQuit 与《CubeResGroupHandle》的实质衔接是：SetQuit 是 CubeResGroupHandle 消息循环的退出信号，usage 与 Wait 解释信号写入后的消费和收尾。
- [Cube核间管理Wait](wait.md)（`same_topic`）：SetQuit 与《Cube核间管理Wait》的实质衔接是：SetQuit 是 CubeResGroupHandle 消息循环的退出信号，usage 与 Wait 解释信号写入后的消费和收尾。
<!-- cannbot:related:end -->
