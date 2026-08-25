---
type: API
title: HCCL Tiling构造函数
description: 用于创建一个Mc2CcTilingConfig对象。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_Tiling/HCCL_Tiling_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# HCCL Tiling构造函数

用于创建一个Mc2CcTilingConfig对象。

参数：
- groupName（输入）：当前通信任务所在的通信域。string类型，支持的最大长度为128字节。
- opType（输入）：表示通信任务类型。uint32_t类型。HCCL API提供HcclCMDType枚举定义作为该参数的取值，具体支持的通信任务类型及取值请参考表2。
- algConfig（输入）：通信算法配置。string类型，支持的最大长度为128字节。
- reduceType（输入）：归约操作类型，仅对有归约操作的通信任务生效。uint32_t类型，取值详见表2。
- dstDataType（输入）：通信任务中输出数据的数据类型。uint8_t类型，该参数的取值范围请参考表1。
