---
type: API
title: BroadCastVecToMMISASI
description: 将矢量数据广播到矩阵中，每个数据块中的每16个元素会被连续复制16次；当前支持的数据传输通路：Unified Buffer-\>L0C Buffer（VECIN/VECCALC/VECOUT-\>CO1）。
  图1 功能示例 !
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/BroadCastVecToMM_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---


# BroadCastVecToMM

将向量数据广播为矩阵格式后搬入L0A或L0B，用于GEMV（矩阵-向量乘）场景。将1维向量数据沿某一维度复制扩展为2维矩阵排布，避免开发者手动构造矩阵数据。

函数原型通过模板参数指定数据类型和广播方向。参数包含源数据Tensor、目的L0A/L0B Tensor、广播参数等。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Reg 归约结果直接 Duplicate 导致末轴 Softmax 偏差](../../../../../runbooks/precision/reduce_lane0_must_be_broadcast_before_vector_normalization.md)（`exemplifies`）：该卡展示标量 lane 广播到向量消费的必要性，可对照广播语义，但目标流水不同。
- [DataCopy](data_copy_l1_to_bias_table.md)（`related`）：DataCopy 与《BroadCastVecToMMISASI》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`related`）：广播搬入仍需满足 Cube 输入对齐和分形约束。
- [Cube计算(ISASI)总体说明](overall_description.md)（`same_topic`）：Load 总页解释 Vec→MM 广播的数据格式、目标 buffer 和限制。
<!-- cannbot:related:end -->
