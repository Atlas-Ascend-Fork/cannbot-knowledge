---
type: API
title: v1版本TilingData（废弃）
description: AI CPU启动下发通信任务前，需获取固定的通信配置Mc2Msg。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling
  Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/v1_TilingData_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# v1版本TilingData（废弃）

AI CPU启动下发通信任务前，需获取固定的通信配置[Mc2Msg](#table4835205712588)。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。

参数：
- preparePosition：设置服务端组装任务的方式，用户需要在Tiling中显式赋值，uint32_t类型，当前支持的取值如下： 1：AI CPU与AI Core通过通信任务机制实现消息传递和任务下发；由AI Core侧通过消息通知时设置为1，即算子中使用HCCL时设置为1。
- sendOff：预留参数，不可配置。
- recvOff：预留参数，不可配置。
- tailSendOff：预留参数，不可配置。
- tailRecvOff：预留参数，不可配置。
约束：
- 算子的Tiling Data结构需要按顺序完整包含Mc2Msg参数。
- AI CPU需获取固定数据结构的通信配置，算子注册Tiling Data时保持该结构的一致性。
- Atlas A3 训练系列产品/Atlas A3 推理系列产品暂不支持该版本TilingData。

<!-- cannbot:related:start -->
## 相关

- [HcclTilingData](tiling_data_struct.md)（`related`）：AI CPU启动下发通信任务前，需获取固定的通信配置［Mc2Msg］(#table4835205712588)。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。；在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；目标卡给出废弃 v1 配置迁移到当前 Kernel 通信 API 的 TilingData 生产消费合同。
<!-- cannbot:related:end -->
