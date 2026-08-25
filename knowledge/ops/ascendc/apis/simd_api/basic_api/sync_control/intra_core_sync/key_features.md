---
type: API
title: 关键特性说明
description: 自动同步功能可减少开发者手动插入同步的工作量，自动同步特性需要了解以下要点：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.synchronization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/intra_core_sync/key_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# 关键特性说明

自动同步功能可减少开发者手动插入同步的工作量，自动同步特性需要了解以下要点：

约束：TPipe-TQue框架编程范式的自动同步功能需满足以下前提条件方可生效
- 使用TPipe-TQue框架编程范式。
- 正确使用EnQue/DeQue、AllocTensor/FreeTensor接口才能保证其自动同步功能正常运作，本条约束对应反例2。

### 支持的同步类型

- 单流水同步

    TPipe-TQue框架编程范式不支持插入单流水同步。
- 多流水同步

    在TPipe-TQue框架编程范式下，框架能够自动插入部分多流水同步，以解决写后读（WAR,Write‑After‑Read）和读后写（RAW,Read‑After‑Write）两类数据依赖，具体原理参考TPipe-TQue框架数据依赖与同步机制。
