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

- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：当前用法页给出新 HcclTiling builder 与 GetTiling 流程。
- [HcclTilingData](tiling_data_struct.md)（`related`）：当前结构化 TilingData 替代固定字段顺序，减少版本耦合。
- [SetCcTiling（废弃）](../hccl_kernel/set_cc_tiling_deprecated.md)（`related`）：旧 Kernel SetCcTiling 消费 V1/V2 数据，迁移时 Host 与 Kernel 两端需同时替换。
- [v2版本TilingData（废弃）](v2_tiling_data_deprecated.md)（`same_topic`）：v2版本TilingData（废弃） 与《v1版本TilingData（废弃）》的实质衔接是：v2 废弃 TilingData 是旧 AI CPU 通信配置布局；v1、SetCcTiling/Init、当前 HcclTilingData 与 SetCcTilingV2 共同给出从旧固定顺序到现行接口的迁移链。
<!-- cannbot:related:end -->
