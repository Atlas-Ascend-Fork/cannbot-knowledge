---
type: API
title: TSCM简介
description: Vector和Cube之间通过队列（Queue）完成任务间通信和同步。TSCM是数据通路的目的地在TSCM Position时，用来管理执行队列相关操作、相关资源的数据结构。TSCM与TQueBind，TQue属于相同类型结构。TSCM定义如下：
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/TSCM_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# TSCM简介

Vector和Cube之间通过队列（Queue）完成任务间通信和同步。TSCM是数据通路的目的地在TSCM Position时，用来管理执行队列相关操作、相关资源的数据结构。TSCM与TQueBind，TQue属于相同类型结构。TSCM定义如下：

<!-- cannbot:related:start -->
## 相关

- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：TSCM简介 与《TSCM输入的矩阵乘》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
- [AllocTensor](alloc_tensor.md)（`same_topic`）：TSCM简介 与《AllocTensor》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
- [DeQue](de_que.md)（`same_topic`）：TSCM简介 与《DeQue》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
- [EnQue](en_que.md)（`same_topic`）：EnQue 与《TSCM简介》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
- [FreeTensor](free_tensor.md)（`same_topic`）：TSCM简介 与《FreeTensor》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
- [TSCM](tscm.md)（`same_topic`）：TSCM 与《TSCM简介》的实质衔接是：TSCM 的 Queue/Buffer 生命周期需要成对 Alloc/Free、EnQue/DeQue 与所有权交接；所选故障卡分别覆盖空取、早释、重取和跨流水复用。
<!-- cannbot:related:end -->
