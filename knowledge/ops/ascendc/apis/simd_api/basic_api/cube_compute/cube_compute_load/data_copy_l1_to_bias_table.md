---
type: API
title: DataCopy
description: 将矩阵计算用到的Bias参数从L1 Buffer搬运到BiasTable Buffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopy_L1ToBiasTable.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# DataCopy（L1到BiasTable搬运）

将L1 Buffer中的bias数据搬运到BiasTable，用于Mmad计算的bias输入。

函数原型通过模板参数指定数据类型。参数包含dstTensor（BiasTable目的）、srcTensor（L1源）、dataCopyParams（搬运参数）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [BroadCastVecToMMISASI](broad_cast_vec_to_mm_isasi.md)（`related`）：DataCopy 与《BroadCastVecToMMISASI》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [Mmad](../mmad_compute/mmad.md)（`related`）：DataCopy 与《Mmad》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [Mmad计算关键特性说明](../mmad_compute_key_features/mmad_compute_key_features.md)（`related`）：DataCopy 与《Mmad计算关键特性说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：DataCopy 与《Mmad辅助配置说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [矩阵计算的搬入总体说明](../../cube_compute_tensor_api/cube_compute_load/overall_description.md)（`related`）：DataCopy 与《矩阵计算的搬入总体说明》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`related`）：DataCopy 与《矩阵计算输入搬运约束》的实质衔接是：L1 到 BiasTable 的 DataCopy 位于 Mmad bias 输入链，CopyL1ToBiasTable、矩阵搬入约束和 Mmad bias 配置直接决定地址与格式是否有效。
- [CopyL1ToBiasTable](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_bias_table.md)（`same_topic`）：DataCopy 的 L1→BiasTable 重载与 CopyL1ToBiasTable 都执行同一条 L1 到 BiasTable 搬运路径；后者以专用命名暴露前者的精确方向合同。
- [L1与BiasTable Buffer数据搬运](../../data_move_guide/l1_bias_table_data_move.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《DataCopy》说明将矩阵计算用到的Bias参数从L1 Buffer搬运到BiasTable Buffer。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
<!-- cannbot:related:end -->
