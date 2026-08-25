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

<!-- cannbot:related:start -->
## 相关

- [FreeTensor早释使队列别名被下一轮DMA覆盖](../../../../../runbooks/precision/reinterpret_tensor_alias_must_outlive_queue_release.md)（`exemplifies`）：DeQue 与《FreeTensor早释使队列别名被下一轮DMA覆盖》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [TBuf 跨 MTE2 与 Vector 须队列交接](../../../../../runbooks/precision/tbuf_mte2_to_vector_requires_queue_handoff.md)（`exemplifies`）：DeQue 与《TBuf 跨 MTE2 与 Vector 须队列交接》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [TQue 输入未释放导致循环 AllocTensor 卡死](../../../../../runbooks/compilation/tque_dequeue_must_end_with_freetensor.md)（`exemplifies`）：DeQue 与《TQue 输入未释放导致循环 AllocTensor 卡死》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [Vector 结果搬出前须经 VECOUT 队列](../../../../../runbooks/precision/vector_results_need_vecout_queue_before_mte3.md)（`exemplifies`）：DeQue 与《Vector 结果搬出前须经 VECOUT 队列》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [TSCM输入的矩阵乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/tscm_input_matmul.md)（`explains`）：Cube/Matmul 消费前用 DeQue 取得已发布 tensor，闭合 TSCM 生产者到矩阵乘输入的同步链。
- [AllocTensor](alloc_tensor.md)（`related`）：DeQue 取回由 EnQue 发布的 TSCM Tensor，并与最终 FreeTensor 构成消费者侧所有权链。
- [FreeTensor](free_tensor.md)（`related`）：DeQue 将 TSCM Tensor 交给消费者，消费完成后才可 FreeTensor，二者明确所有权释放时点。
- [EnQue](en_que.md)（`same_topic`）：EnQue 与《DeQue》的实质衔接是：TSCM EnQue 把已分配 tensor 的所有权推入队列，DeQue 取回，AllocTensor/FreeTensor 和 TSCM 概述闭合队列容量与资源生命周期。
- [TSCM](tscm.md)（`same_topic`）：DeQue 与《TSCM》的实质衔接是：TSCM DeQue 必须与 EnQue、Alloc/Free 和所有权交接配套；所选故障卡直接覆盖空队列、重复 DeQue、早释和跨流水交接。
- [TSCM简介](tscm_intro.md)（`same_topic`）：TSCM简介 与《DeQue》的实质衔接是：TSCM 用 Queue 在 Vector/Cube 间交接 tensor；Alloc/Free、EnQue/DeQue 和矩阵乘示例共同闭合资源与所有权生命周期。
<!-- cannbot:related:end -->
