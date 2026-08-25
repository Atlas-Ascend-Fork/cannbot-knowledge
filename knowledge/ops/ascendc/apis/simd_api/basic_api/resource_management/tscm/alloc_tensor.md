---
type: API
title: AllocTensor
description: 从TSCM中分配tensor，大小为InitBuffer时设置的每块内存长度，分配内容可能为随机值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TSCM/AllocTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AllocTensor

头文件路径为："basic_api/kernel_tpipe.h"。

从TSCM中分配tensor，tensor所占大小为InitBuffer时设置的每块内存长度。注意，分配的tensor内容并非全0，可能会是随机值。

参数：T: 待获取Tensor的数据类型，支持的类型请见LocalTensor相关描述。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：指南实现需先从 TSCM 分配输入 tensor，再写入并交给 Matmul；AllocTensor 定义这块片上缓冲的取得方式。
- [DeQue](de_que.md)（`related`）：DeQue 取回由 EnQue 发布的 TSCM Tensor，并与最终 FreeTensor 构成消费者侧所有权链。
- [EnQue](en_que.md)（`related`）：AllocTensor 后通过 EnQue 发布 TSCM Tensor，明确随机初始内容不能在入队前被当作零值使用。
- [FreeTensor](free_tensor.md)（`same_topic`）：TSCM FreeTensor 与 AllocTensor 必须成对管理同一 Tensor 资源，闭合分配生命周期。
- [TSCM简介](tscm_intro.md)（`same_topic`）：TSCM简介 与《AllocTensor》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
<!-- cannbot:related:end -->
