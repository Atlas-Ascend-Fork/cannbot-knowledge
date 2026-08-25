---
type: API
title: EnableMultiCoreSplitK
description: 多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/EnableMultiCoreSplitK.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# EnableMultiCoreSplitK

多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。

函数原型：void EnableMultiCoreSplitK(bool flag)

参数：
- flag（输入）：是否开启切K轴。/true：开启切K轴。/false：不开启切K轴。

约束：
- 在算子中使用该接口时，获取C矩阵结果时仅支持输出到Global Memory。
- 在算子中使用该接口时，需在Kernel侧代码中首次将C矩阵分片的结果写入Global Memory之前，先清零Global Memory，随后在获取C矩阵分片的结果时，再开启AtomicAdd累加。如果不预先清零Global Memory，可能会因为累加Global Memory中原始的无效数据而产生精度问题。
- 在算子中使用该接口时，不支持Bias参与矩阵乘计算。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启多核切K](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_multi_core_split_k.md)（`explains`）：指南给出 EnableMultiCoreSplitK 的适用 shape、调用时点和完整 Kernel 配套：C 只写 GM、首次写前清零并用 AtomicAdd、禁止 Bias，同时说明为何 K 大而 M/N 小时能提升并行度。
- [多核对齐切分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`explains`）：多核对齐切分 与《EnableMultiCoreSplitK》的实质衔接是：对齐切分按可用核数设置 SetDim/NumBlocks，并与非对齐尾块、N 对齐、Channel 拆分、多核 K 切分及临时空间计算共同决定实际 Matmul 分工。
- [GetCoreNum](get_core_num.md)（`related`）：启用 SplitK 会改变实际参与核数和归并策略。
- [Matmul Tiling类](matmul_tiling.md)（`related`）：SplitK 是总 tiling 流程中的多核策略分支。
- [SetDim](set_dim.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《EnableMultiCoreSplitK》具体提供“多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetSingleRange](set_single_range.md)（`related`）：《SetSingleRange》处理“设置singleCoreM/singleCoreN/singleCoreK的最大值与最小值。”。《EnableMultiCoreSplitK》明确“多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。”，可直接用于核对Matmul Tiling 单范围/shape/split 参数写入、查询和最终 GetTiling 产出合同。
- [SetSplitK](set_split_k.md)（`same_topic`）：SetSplitK 与《EnableMultiCoreSplitK》的实质衔接是：SplitK 必须与 multi-core split、split range、single range/shape、core 数和 AtomicAdd 汇合配置一致。
<!-- cannbot:related:end -->
