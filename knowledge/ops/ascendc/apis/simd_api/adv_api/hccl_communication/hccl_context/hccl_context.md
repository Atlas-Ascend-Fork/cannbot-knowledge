---
type: API
title: HCCL Context
description: 提供HCCL通信上下文管理接口，包含HCCL Context简介、SetHcclContext、GetHcclContext等方法。
tags: [task.lookup, topic.data_movement.communication.collective_communication]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/HCCL_communication/HCCL-Context/HCCL-Context.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# HCCL Context

提供HCCL通信上下文管理接口，包含HCCL Context简介、SetHcclContext、GetHcclContext等方法。

设置通算融合算子每个通信域对应的context（消息区）地址。

本接口组包含 SetHcclContext，辅助接口包括 GetHcclContext。

本接口属于 HCCL 集合通信接口，用于多卡间的通信操作。

约束：当前最多只支持2个通信域。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
