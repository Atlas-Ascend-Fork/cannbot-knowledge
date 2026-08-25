---
type: API
title: FreeMessage
description: 在自定义的回调函数逻辑中，完成消息处理后，调用该接口，刷新消息状态为FREE；或者待消息状态为指定状态waitState时，刷新消息状态为FREE。消息状态的介绍可以参考表2中的参数msgState。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/FreeMessage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# FreeMessage

在回调函数中完成消息处理后，刷新消息状态为 FREE。两个重载：直接刷新，或等待消息状态为指定 waitState 后再刷新。

原型：`uint16_t FreeMessage(__gm__ CubeMsgType* msg)` 和 `uint16_t FreeMessage(__gm__ CubeMsgType* msg, CubeMsgState waitState)`。参数 msg 为消息空间地址，waitState 为等待的消息状态。返回 uint16_t。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [Cube核间管理Wait](wait.md)（`related`）：Wait 确认消息处理后仍需 FreeMessage 归还消息资源，否则同步槽生命周期不闭合。
- [AllocMessage](alloc_message.md)（`same_topic`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《FreeMessage》明确“在自定义的回调函数逻辑中，完成消息处理后，调用该接口，刷新消息状态为FREE；或者待消息状态为指定状态waitState时，刷新消息状态为FREE。消息状态的介绍可以参考表2中的参数msgState。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CubeResGroupHandle](cube_res_group_handle.md)（`same_topic`）：FreeMessage 与《CubeResGroupHandle》的实质衔接是：FreeMessage 释放由 AllocMessage 取得并经 PostMessage 流转的消息，CubeResGroupHandle 使用说明给出完整状态生命周期。
- [PostMessage](post_message.md)（`same_topic`）：FreeMessage 与《PostMessage》的实质衔接是：FreeMessage 释放由 AllocMessage 取得并经 PostMessage 流转的消息，CubeResGroupHandle 使用说明给出完整状态生命周期。
<!-- cannbot:related:end -->
