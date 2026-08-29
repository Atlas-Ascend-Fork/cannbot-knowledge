---
type: API
title: HCCL Tiling使用说明
description: 说明 HCCL 通信任务的 TilingData、Mc2InitTiling、Mc2CcTiling 及临时空间配置方式。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling_usage.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling使用说明

在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。本节TilingData结构体包括Mc2InitTiling和Mc2CcTiling，这两个结构体均通过调用GetTiling接口返回。其中，Mc2CcTiling为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个Mc2CcTiling参数（最多支持定义8个）。

本接口组包含 TilingData结构体, v1版本TilingData（废弃）, v2版本TilingData（废弃）, TilingData结构体。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetTiling](get_tiling.md)（`related`）：在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；获取Mc2InitTiling参数和Mc2CcTiling参数。。使用说明规定由 Tiling 组装并下传通信配置，GetTiling 正是生成 Mc2InitTiling 与 Mc2CcTiling 的具体 Host 接口。
- [HCCL Tiling构造函数](hccl_tiling_constructor.md)（`related`）：用于创建一个Mc2CcTilingConfig对象；Mc2CcTiling为具体每个通信任务的参数配置；连接对象构造与 GetTiling/Kernel 消费。
- [HcclTilingData](tiling_data_struct.md)（`related`）：其中，［Mc2CcTiling］(#table678914014562)为具体每个通信任务的参数配置，当算子中有多个通信任务时，可定义多个［Mc2CcTiling］(#table678914014562)参数：（最多支持定义8个）。；在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；使用说明把结构体的多通信任务参数放入 Host 组装到 Kernel 消费的数据流。
<!-- cannbot:related:end -->
