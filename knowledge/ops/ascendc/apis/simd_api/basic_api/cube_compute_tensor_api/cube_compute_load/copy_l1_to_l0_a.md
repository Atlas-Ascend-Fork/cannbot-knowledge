---
type: API
title: CopyL1ToL0A
description: 通过Tensor API的Copy接口将L1 Buffer中的左矩阵数据搬运到L0A Buffer，支持转置搬运和Img2Col卷积展开。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_L1ToL0A.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（L1到L0A Buffer数据搬运）

通过统一Copy接口将L1 Buffer数据搬运到L0A Buffer，用于矩阵计算左矩阵A输入。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

支持场景：连续数据搬入、随路格式转换（L1的NZ/ZN格式到L0A的Fractal格式）、Batch多矩阵搬入。函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [AscCopyUb2l1](../../../c_api/vector_data_move/asc_copy_ub2l1.md)（`related`）：进入 L1 后可继续搬入 L0A 给 Cube 消费。
- [CopyGmToL1](copy_gm_to_l1.md)（`related`）：Cube Tensor 数据链先用 CopyGmToL1 把矩阵从 GM 搬到 L1，再由 focal CopyL1ToL0A 装入 L0A，二者共享 Layout 驱动的分形搬运契约。
- [CopyL1ToBiasTable](copy_l1_to_bias_table.md)（`related`）：矩阵 A 搬入 L0A，不应与 bias 数据目标混用。
- [CopyL1ToL0B](copy_l1_to_l0_b.md)（`related`）：L0A/L0B 分别承载矩阵左右操作数，侧别必须匹配。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《CopyL1ToL0A》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算输入搬运约束](../../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《CopyL1ToL0A》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
