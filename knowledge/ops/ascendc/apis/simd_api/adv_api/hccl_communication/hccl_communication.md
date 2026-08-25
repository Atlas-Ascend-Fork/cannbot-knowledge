---
type: API
title: HCCL通信类
description: 汇总Ascend C SIMD高阶API中的HCCL集合通信接口，包含Kernel侧、Tiling侧及HCCL Context管理接口。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL_communication.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# HCCL通信类

汇总Ascend C SIMD高阶API中的HCCL集合通信接口，包含Kernel侧、Tiling侧及HCCL Context管理接口。

本接口组包含 HCCL Kernel侧接口, HCCL Tiling侧接口, HCCL Context。

本接口属于 HCCL 集合通信接口，用于多卡间的通信操作。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
