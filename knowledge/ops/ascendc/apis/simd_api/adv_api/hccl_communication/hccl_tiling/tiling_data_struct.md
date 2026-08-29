---
type: API
title: HcclTilingData
description: HCCL通信Tiling配置结构体，包含Mc2InitTiling和Mc2CcTiling，通过GetTiling接口返回，最多支持8个通信任务。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/TilingData_struct.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# HcclTilingData

在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。本节TilingData结构体包括[Mc2InitTiling](#table4835205712588)和[Mc2CcTiling](#table678914014562)，这两个结构体均通过调用GetTiling接口返回。其中，[Mc2CcTiling](#table678914014562)为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个[Mc2CcTiling](#table678914014562)参数：（最多支持定义8个）。

参数：
- reserved（初始化通信任务配置。uint8_t*类型，支持最大长度64字节，该结构体仅支持通过接口GetTiling获取。
- reserved：各通信域中每个通信任务的参数配置。uint8_t*类型，支持最大长度280字节，该结构体仅支持通过接口GetTiling获取。注意，最多支持配置8个通信任务。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：reserved：各通信域中每个通信任务的参数配置。uint8_t*类型，支持最大长度280字节，该结构体仅支持通过接口GetTiling获取。注意，最多支持配置8个通信任务。；获取Mc2InitTiling参数和Mc2CcTiling参数。；GetTiling 是结构体卡明确规定的唯一生产接口，并返回其两个组成参数。
- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：其中，［Mc2CcTiling］(#table678914014562)为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个［Mc2CcTiling］(#table678914014562)参数：（最多支持定义8个）。；在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；使用说明把结构体的多通信任务参数放入 Host 组装到 Kernel 消费的数据流。
- [v1版本TilingData（废弃）](v1_tiling_data_deprecated.md)（`related`）：AI CPU启动下发通信任务前，需获取固定的通信配置［Mc2Msg］(#table4835205712588)。在算子实现中，由Tiling组装通信配置项，通过配置固定参数和固定参数顺序的Tiling Data，将通信配置信息在调用AI CPU通信接口时传递给AI CPU。；在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；目标卡给出废弃 v1 配置迁移到当前 Kernel 通信 API 的 TilingData 生产消费合同。
<!-- cannbot:related:end -->
