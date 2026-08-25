---
type: API
title: EnQue
description: 将tensor push到TSCM队列中，入队成功返回true，队列已满返回false。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/EnQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# EnQue

将tensor push到TSCM队列中，入队成功返回true，队列已满返回false。

将tensor push到队列。

本接口属于资源管理接口，用于管理 Queue、Buffer 等计算资源。

支持的数据类型为 LocalTensor 支持的常见类型（half/float/int等）。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

返回值：- true - 表示Tensor加入Queue成功 - false - 表示Queue已满，入队失败

支持的硬件型号：Ascend 950PR/Ascend 950DT。

<!-- cannbot:related:start -->
## 相关

- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：Vector 侧写完 TSCM tensor 后需 EnQue 发布，才能让 Cube 侧按队列同步消费。
- [AllocTensor](alloc_tensor.md)（`related`）：AllocTensor 后通过 EnQue 发布 TSCM Tensor，明确随机初始内容不能在入队前被当作零值使用。
- [DeQue](de_que.md)（`same_topic`）：EnQue 与《DeQue》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
- [FreeTensor](free_tensor.md)（`same_topic`）：EnQue 与《FreeTensor》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
- [TSCM简介](tscm_intro.md)（`same_topic`）：EnQue 与《TSCM简介》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
<!-- cannbot:related:end -->
