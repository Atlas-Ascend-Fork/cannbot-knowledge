---
type: API
title: DeQue
description: 将tensor从TSCM队列中取出，用于后续处理。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/DeQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# DeQue

将tensor从TSCM队列中取出，用于后续处理。

将tensor从队列中取出，用于后续处理。

本接口属于资源管理接口，用于管理 Queue、Buffer 等计算资源。

支持的数据类型为 LocalTensor 支持的常见类型（half/float/int等）。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

返回值：从队列中取出的LocalTensor。

支持的硬件型号：Ascend 950PR/Ascend 950DT。
