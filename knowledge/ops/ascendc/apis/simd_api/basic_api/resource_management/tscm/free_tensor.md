---
type: API
title: FreeTensor
description: 释放TSCM中指定的Tensor资源。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/FreeTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# FreeTensor

头文件路径为："basic_api/kernel_tpipe.h"。

释放TSCM中的指定Tensor。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [DeQue](de_que.md)（`related`）：DeQue 将 TSCM Tensor 交给消费者，消费完成后才可 FreeTensor，二者明确所有权释放时点。
- [AllocTensor](alloc_tensor.md)（`same_topic`）：TSCM FreeTensor 与 AllocTensor 必须成对管理同一 Tensor 资源，闭合分配生命周期。
- [EnQue](en_que.md)（`same_topic`）：EnQue 与《FreeTensor》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
- [TSCM简介](tscm_intro.md)（`same_topic`）：TSCM简介 与《FreeTensor》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
<!-- cannbot:related:end -->
