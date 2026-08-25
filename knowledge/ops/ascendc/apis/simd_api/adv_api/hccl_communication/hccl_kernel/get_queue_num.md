---
type: API
title: GetQueueNum
description: 获取BatchWrite通信任务的通信队列数量。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Kernel/GetQueueNum.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a3]
---

# GetQueueNum

获取BatchWrite通信任务的通信队列数量。

函数原型：__aicore__ inline uint16_t GetQueueNum()

返回值：BatchWrite通信任务的通信队列数量。

支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品。不支持：Ascend 950PR/Ascend 950DT、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AlltoAllvWrite](allto_allv_write.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《AlltoAllvWrite》说明集合通信AlltoAllvWrite任务下发接口，支持定制发送偏移和数据大小，实现卡间数据的点对点写入。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [AssignQueue](../../../basic_api/cube_group_mgmt/cube_res_group_handle/assign_queue.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《AssignQueue》说明AssignQueue 接口，用于 AIV 绑定 CubeResGroupHandle 中某一个消息队列的序号。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [BatchWrite](batch_write.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《BatchWrite》说明集合通信BatchWrite任务下发接口，实现点对点批量数据传输，可同时将多份数据发送到不同Global Memory地址。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [Commit（HCCL集合通信）](commit.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《Commit（HCCL集合通信）》说明非细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的任务一次。细粒度通信时，每调用一次本接口，则通知服务端可以执行handleId对应的步长长度的子通信任务。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [Finalize（HCCL集合通信）](finalize.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《Finalize（HCCL集合通信）》说明通知服务端后续无通信任务，执行结束后退出。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [HCCL Kernel侧接口](hccl_kernel.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《HCCL Kernel侧接口》说明提供HCCL集合通信的Kernel侧接口，包含InitV2、SetCcTilingV2、AllReduce、AllGather、ReduceScatter、BatchWrite等方法。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [HCCL使用说明](hccl_usage.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《HCCL使用说明》说明Ascend C提供一组HCCL通信类高阶API，方便算子Kernel开发用户在AI Core侧灵活管理通算融合算子中计算与通信任务的执行顺序。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [HCCL集合通信Wait](wait.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《HCCL集合通信Wait》说明阻塞AI Core，非细粒度通信时，等待handleId对应的通信任务完成，细粒度通信时，等待handleId对应的步长长度的子通信任务完成。handleId调用Wait接口的顺序，须和Prepare接口一致。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [InitV2](init_v2.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《InitV2》说明HCCL客户端初始化接口。该接口默认在所有核上工作，用户也可以在调用前通过GetBlockIdx指定其在某一个核上运行。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [QueueBarrier](queue_barrier.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《QueueBarrier》说明阻塞服务端上指定队列的BatchWrite通信任务，直到指定范围内所有队列上的任务完成执行，从而实现指定范围内队列的同步。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [SetCommBlockNum](../hccl_tiling/set_comm_block_num.md)（`related`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《SetCommBlockNum》说明设置参与BatchWrite通信的核数。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
- [SetQueueNum](../hccl_tiling/set_queue_num.md)（`same_topic`）：《GetQueueNum》说明获取BatchWrite通信任务的通信队列数量。；《SetQueueNum》说明设置每个向服务端下发任务的核上的BatchWrite通信队列数量。。二者在通信队列数量的查询与设置、BatchWrite/AlltoallvWrite发任务、Commit/Wait及Finalize构成同一HCCL任务生命周期上存在可执行的直接衔接。
<!-- cannbot:related:end -->
