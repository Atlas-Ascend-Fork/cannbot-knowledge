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
