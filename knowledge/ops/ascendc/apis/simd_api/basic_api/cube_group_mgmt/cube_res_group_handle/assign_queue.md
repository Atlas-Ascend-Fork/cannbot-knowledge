---
type: API
title: AssignQueue
description: AssignQueue 接口，用于 AIV 绑定 CubeResGroupHandle 中某一个消息队列的序号。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_group_mgmt_ISASI/CubeResGroupHandle/AssignQueue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2]
---

# AssignQueue

AIV 绑定 CubeResGroupHandle 中某个消息队列的序号。

原型：`__aicore__ inline void AssignQueue(uint8_t queueIdIn)`。参数 queueIdIn 为消息队列序号。支持 950/a2。

<!-- cannbot:related:start -->
## 相关

- [AllocMessage](alloc_message.md)（`related`）：《AllocMessage》处理“AIV从消息队列里申请消息空间，用于存放消息结构体，返回当前申请的消息空间的地址。消息队列的深度固定为4，申请消息空间的顺序为自上而下，然后循环。当消息队列指针指向的消息空间为FREE状态时，AllocMessage返回空间的地址，否则循环等待，直到当前空间的状态为FREE。 图1 AllocMessage示意图”。《AssignQueue》明确“AssignQueue 接口，用于 AIV 绑定 CubeResGroupHandle 中某一个消息队列的序号。”，可直接用于核对AllocMessage/PostMessage/FreeMessage 生命周期、Cube 资源组句柄和 KFC workspace 合同。
- [CreateCubeResGroup](create_cube_res_group.md)（`related`）：AssignQueue 作用于已创建且完成消息队列/事件分配的 CubeResGroupHandle，CreateCubeResGroup 是推荐的安全上游构造方式。
- [GetQueueNum](../../../adv_api/hccl_communication/hccl_kernel/get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《AssignQueue》说明AssignQueue 接口，用于 AIV 绑定 CubeResGroupHandle 中某一个消息队列的序号。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [PostMessage](post_message.md)（`related`）：AssignQueue 选定 AIV 对应队列，随后 PostMessage 将 AllocMessage 填好的消息沿该队列发送给 AIC。
<!-- cannbot:related:end -->
