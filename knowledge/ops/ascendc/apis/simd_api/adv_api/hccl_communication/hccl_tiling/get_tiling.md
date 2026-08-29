---
type: API
title: GetTiling
description: 获取Mc2InitTiling参数和Mc2CcTiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/GetTiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetTiling

获取Mc2InitTiling参数和Mc2CcTiling参数。

参数：
- tiling（输出）：Tiling结构体存储的Tiling信息。

返回值：- 返回值为0，则tiling计算成功，该Tiling结构体的值可以用于后续计算。

<!-- cannbot:related:start -->
## 相关

- [HCCL Tiling使用说明](hccl_tiling_usage.md)（`related`）：在算子实现中，由Tiling组装通信配置项，核函数实现时将Tiling配置项通过入参传递给Kernel侧通信API做通信计算。；获取Mc2InitTiling参数和Mc2CcTiling参数。。使用说明规定由 Tiling 组装并下传通信配置，GetTiling 正是生成 Mc2InitTiling 与 Mc2CcTiling 的具体 Host 接口。
- [HcclTilingData](tiling_data_struct.md)（`related`）：reserved：各通信域中每个通信任务的参数配置。uint8_t*类型，支持最大长度280字节，该结构体仅支持通过接口GetTiling获取。注意，最多支持配置8个通信任务。；获取Mc2InitTiling参数和Mc2CcTiling参数。；GetTiling 是结构体卡明确规定的唯一生产接口，并返回其两个组成参数。
- [SetCcTilingV2](../hccl_kernel/set_cc_tiling_v2.md)（`related`）：Host Tiling 接口“获取Mc2InitTiling参数和Mc2CcTiling参数。”；Device 接口说明“Mc2CcTiling在Host侧计算得出”，因此 GetTiling 产出的 Mc2CcTiling 正是 SetCcTilingV2 在 Kernel 侧消费的配置来源。
<!-- cannbot:related:end -->
