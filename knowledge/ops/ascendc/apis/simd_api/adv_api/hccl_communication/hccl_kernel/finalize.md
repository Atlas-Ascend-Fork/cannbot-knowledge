---
type: API
title: Finalize（HCCL集合通信）
description: 通知服务端后续无通信任务，执行结束后退出。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/Finalize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Finalize（HCCL集合通信）

通知服务端后续无通信任务，执行结束后退出。

函数原型：
template <bool sync = true>
__aicore__ inline void Finalize()

参数：
- sync（输入）：是否需要等待服务端的通信完成。bool类型，参数取值如下：true：默认值，表示客户端将检测并等待最后一个通信任务完成。/false：表示客户端发送Finalize通知后，不等待服务端通信任务完成即退出。

约束：
- 调用本接口前确保已调用过InitV2和SetCcTilingV2接口。
- 本接口在AIC核或者AIV核上调用必须与对应的Prepare接口的调用核保持一致。
- 调用Finalize()前，若需要保证通信任务完成，必须先完成同步；否则客户端直接退出后，无法保证数据传输完成。多队列BatchWrite场景需先对所有队列调用QueueBarrier接口，等待队列上的BatchWrite任务完成后再调用Finalize\()，请参见BatchWrite的多个队列的点对点通信调用示例。
- Finalize为终止接口，调用后服务端开始退出，当前Hccl对象不可再次用于通信。如需继续通信，需重新创建Hccl对象并调用InitV2接口初始化。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AllReduce](all_reduce.md)（`related`）：AllReduce 与《Finalize（HCCL集合通信）》的实质衔接是：AllReduce 必须在 InitV2/SetCcTilingV2 后下发，并通过 Commit、Query/Wait、Finalize 完成任务；模板、reduce 类型和使用说明约束通信执行链。
- [BatchWrite](batch_write.md)（`related`）：《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。；《Finalize（HCCL集合通信）》说明通知服务端后续无通信任务，执行结束后退出。。二者在BatchWrite的多目标点对点任务依赖通信队列数量，进入Commit、Query/Wait和Finalize的HCCL任务生命周期上存在可执行的直接衔接。
- [Commit（HCCL集合通信）](commit.md)（`related`）：Finalize（HCCL集合通信） 与《Commit（HCCL集合通信）》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [GetQueueNum](get_queue_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《Finalize（HCCL集合通信）》说明通知服务端后续无通信任务，执行结束后退出。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [HCCL集合通信Wait](wait.md)（`related`）：Finalize（HCCL集合通信） 与《HCCL集合通信Wait》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [InitV2](init_v2.md)（`related`）：Finalize（HCCL集合通信） 与《InitV2》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [QueueBarrier](queue_barrier.md)（`related`）：Finalize（HCCL集合通信） 与《QueueBarrier》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [SetCcTilingV2](set_cc_tiling_v2.md)（`related`）：Finalize（HCCL集合通信） 与《SetCcTilingV2》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [AlltoAllvWrite](allto_allv_write.md)（`same_topic`）：AlltoAllvWrite 与《Finalize（HCCL集合通信）》的实质衔接是：AlltoAllvWrite 的字节偏移、大小和 window 地址依赖 rank/window 查询，且必须在 InitV2/SetCcTilingV2 后通过 Commit、Query/Wait、Finalize 完成 HCCL 任务。
- [HCCL Kernel侧接口](hccl_kernel.md)（`same_topic`）：焦点处理HCCL Kernel 的初始化、任务提交查询等待和资源回收；Finalize（HCCL集合通信）正文界定“通知服务端后续无通信任务，执行结束后退出”。候选承担 HCCL 使用正文中的 Init、Iterate、Commit/Query/Wait、Finalize 或 context 设置，runbook 则复现同一 HCCL 同步失效。
- [HCCL使用说明](hccl_usage.md)（`same_topic`）：Finalize（HCCL集合通信） 与《HCCL使用说明》的实质衔接是：Finalize 只能在 InitV2 和 SetCcTilingV2 之后终止 HCCL 对象；普通任务需先 Commit/Wait，多个 BatchWrite 队列需逐队列 QueueBarrier，使用说明明确终止后对象不可复用。
- [Init（废弃）](init_deprecated.md)（`same_topic`）：焦点处理废弃 HCCL Init 向 InitV2/SetCcTilingV2 迁移的生命周期；Finalize（HCCL集合通信）正文说明“通知服务端后续无通信任务，执行结束后退出”。候选给出旧接口的一一替代、通信配置迁移或最终资源回收步骤。
<!-- cannbot:related:end -->
