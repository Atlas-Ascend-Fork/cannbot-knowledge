---
type: API
title: TQue简介
description: 流水任务之间通过队列（Queue）完成任务间通信和同步。TQue是用来执行队列相关操作、管理相关资源的数据结构。TQue继承自TQueBind父类，继承关系如下：
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/TQue_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms: ['950', a2, a3]
---

# TQue简介

流水任务之间通过队列（Queue）完成任务间通信和同步。TQue是用来执行队列相关操作、管理相关资源的数据结构。TQue继承自TQueBind父类，继承关系如下：

本接口属于资源管理接口，用于管理 Queue、Buffer 等计算资源。

## 模板参数

| 参数 | 含义 |
|---|---|
| `pos` | 队列的逻辑位置，使用 `TPosition` 中的 `VECIN`、`VECOUT`、`A1`、`A2`、`B1`、`B2`、`CO1` 或 `CO2`。 |
| `depth` | 同一队列在没有 `DeQue` 的情况下允许连续 `EnQue` 的次数；若连续入队 `n` 次，深度至少为 `n`。 |

队列深度与 double buffer 是不同维度：深度为 1 时仍可开启 double buffer。非 Tensor 原地操作通常建议将深度设为 1；Tensor 原地操作按接口约束将深度设为 0。实际代码必须保持 `AllocTensor → EnQue → DeQue → FreeTensor` 的所有权顺序。

<!-- cannbot:related:start -->
## 相关

- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：“实际代码必须保持 `AllocTensor → EnQue → DeQue → FreeTensor` 的所有权顺序”与“全部重复更新都在 UB 内按原始 `k` 顺序合并，最后只以连续 DMA 写回 GM”把 TQue 生命周期约束落实到重复更新的有序 UB 合并实现。
- [VacantInQue](vacant_in_que.md)（`related`）：查询队列是否已满。 约束：该接口不支持Tensor原地操作，即TQue的depth设置为0的场景。；队列深度与 double buffer 是不同维度：深度为 1 时仍可开启 double buffer。非 Tensor 原地操作通常建议将深度设为 1；Tensor 原地操作按接口约束将深度设为 0。；VacantInQue 的可用性取决于 depth 是否为 0，TQue 概念卡给出原地操作与 depth 取值的配置边界。
<!-- cannbot:related:end -->
