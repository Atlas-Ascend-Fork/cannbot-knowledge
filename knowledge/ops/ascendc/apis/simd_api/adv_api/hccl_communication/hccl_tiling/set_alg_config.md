---
type: API
title: SetAlgConfig
description: uint32_t SetAlgConfig(const std::string& algConfig)
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/SetAlgConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetAlgConfig

uint32_t SetAlgConfig(const std::string& algConfig)

设置通信算法。

本接口属于 HCCL 集合通信 Tiling 接口，用于配置多卡通信参数。

参数说明：algConfig：输入 通信算法配置。string类型，支持的最大长度为128字节。

返回值：-   0表示设置成功。
-   非0表示设置失败。
