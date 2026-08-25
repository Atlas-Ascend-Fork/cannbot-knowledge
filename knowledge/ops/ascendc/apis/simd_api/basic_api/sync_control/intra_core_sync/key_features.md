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

<!-- cannbot:related:start -->
## 相关

- [DataSyncBarrier](data_sync_barrier_isasi.md)（`related`）：需要更广数据可见性时使用 DataSyncBarrier，代价和范围均更大。
- [PipeBarrier](pipe_barrier_isasi.md)（`related`）：同流水排空使用 PipeBarrier，不应误用跨流水 event。
- [SetFlag/WaitFlag](set_flag_wait_flag_isasi.md)（`related`）：明确 producer/consumer 流水时 flag/wait 建立定向依赖。
- [关键特性说明](../inter_core_sync/key_features.md)（`related`）：核间同步特性作用于不同核，不能用核内机制替代。
- [核内同步能力概述](intra_core_sync_overview.md)（`same_topic`）：概览解释 key features 中 event、barrier、mutex 的同步域和适用条件。
<!-- cannbot:related:end -->
