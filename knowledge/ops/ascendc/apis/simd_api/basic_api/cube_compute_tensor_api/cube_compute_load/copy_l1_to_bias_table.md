---
type: API
title: CopyL1ToBiasTable
description: 通过Tensor API的Copy接口将L1 Buffer中的bias数据搬运到BiasTable Buffer，作为Mmad计算的bias输入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToBiasTable.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到BiasTable数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到BiasTable，用于矩阵计算的bias输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [CopyL1ToFixpipe](copy_l1_to_fixpipe.md)（`related`）：BiasTable 和 Fixpipe 是不同辅助 buffer，后续消费单元决定目标。
- [CopyL1ToL0A](copy_l1_to_l0_a.md)（`related`）：矩阵 A 搬入 L0A，不应与 bias 数据目标混用。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_l1_to_bias_table.md)（`same_topic`）：DataCopy 的 L1→BiasTable 重载与 CopyL1ToBiasTable 都执行同一条 L1 到 BiasTable 搬运路径；后者以专用命名暴露前者的精确方向合同。
- [L1与BiasTable Buffer数据搬运](../../data_move_guide/l1_bias_table_data_move.md)（`same_topic`）：《L1与BiasTable Buffer数据搬运》说明DataCopy能够实现L1 Buffer至BiasTable Buffer的连续数据搬运，数据搬运时格式和内容保持不变。；《CopyL1ToBiasTable》说明通过Tensor API的Copy接口将L1 Buffer中的bias数据搬运到BiasTable Buffer，作为Mmad计算的bias输入。。二者在L1到BiasTable的连续搬运由C++/Tensor/C三层等价接口实现，并受Bias类型和数据通路约束上存在可执行的直接衔接。
<!-- cannbot:related:end -->
