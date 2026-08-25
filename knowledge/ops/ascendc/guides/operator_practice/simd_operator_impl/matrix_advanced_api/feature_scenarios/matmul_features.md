---
type: Guide
title: Matmul特性介绍
description: 除了前述基础知识和算子实现中介绍的基本计算能力外，Matmul矩阵编程还提供了适用于不同场景的处理能力及多种功能，具体场景和功能列于下表中，详细内容请见后续章节。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matmul_features.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# Matmul特性介绍

除了前述基础知识和算子实现中介绍的基本计算能力外，Matmul矩阵编程还提供了适用于不同场景的处理能力及多种功能，具体场景和功能列于下表中，详细内容请见后续章节。
Matmul功能特性表
BatchMatmu功能l特性表

<!-- cannbot:related:start -->
## 相关

- [SIMD算子实现基础知识](../basics.md)（`related`）：基础数据流之后需要按输入位置、输出布局、切分与量化需求选择 Matmul 特性；特性页承接这一设计决策。
- [算子实现](../operator_impl.md)（`related`）：算子实现 与《Matmul特性介绍》的实质衔接是：该指南的核心是 host tiling→kernel Matmul 对象→Set A/B→Iterate/IterateAll→End；耦合模式、异步迭代与 CUBE_ONLY 故障直接约束实现选择。
- [MxMatmul场景](mx_matmul_scenario.md)（`same_topic`）：MxMatmul场景 与《Matmul特性介绍》的实质衔接是：MxMatmul 需要 MmadMx/AscMmadMx、scaleA/scaleB 及类型/Mad 配置共同实现 C=(scaleA*A)*(scaleB*B)+Bias，量化输出材料补充缩放矩阵契约。
- [单次矩阵乘局部输出](single_matmul_local_output.md)（`same_topic`）：单次矩阵乘局部输出 与《Matmul特性介绍》的实质衔接是：Partial Output 只允许 MDL 的 Iterate+GetTensorC 连续写，跳过 K 累加且禁用 Bias/IterateAll；Matmul Kernel、异步/对齐和精度材料直接约束该链。
- [多核对齐切分](multi_core_aligned_split.md)（`same_topic`）：多核对齐切分 与《Matmul特性介绍》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [矩阵乘输出的N方向对齐](matmul_output_n_alignment.md)（`same_topic`）：矩阵乘输出的N方向对齐 与《Matmul特性介绍》的实质衔接是：N 方向非对齐输出依赖 ND_ALIGN 布局和 GetTensorC 搬出；局部输出、Matmul 特性、多核对齐/非对齐切分与精度 FAQ直接约束输出形状和尾块。
- [矩阵向量乘](matrix_vector_multiply.md)（`same_topic`）：矩阵向量乘 与《Matmul特性介绍》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
<!-- cannbot:related:end -->
