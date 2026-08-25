---
type: API
title: SetDim
description: 设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Tiling/SetDim.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetDim

设置多核Matmul时，参与运算的核数。不同场景下的设置规则如下： - 纯Cube模式（只有矩阵计算） SetDim设置当前AI处理器可用的核数，通过Tiling计算得到执行Matmul计算实际使用的核数，实际使用的核数小于等于AI处理器可用的核数。SetSimdNumBlocks按照实际使用的核数由用户进行配置，SetSimdNumBlocks加载的核全部用于Matmul API的计算。

参数：
- dim（输入）：多核Matmul tiling计算时，可以使用的核数。注意，MIX模式下，该参数取值小于等于耦合模式下启动的AICore核数或者分离模式下启动的AIV核数。

返回值：-1表示设置失败； 0表示设置成功。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启纯Cube模式](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_pure_cube.md)（`explains`）：《SetDim》给出“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”；该约束/探针可直接复现、解释或前置验证《Matmul高阶API开启纯Cube模式》中的“本案例呈现了在矩阵乘算子场景中，开启Matmul高阶API的纯Cube模式对算子性能的提升效果。如下图所示，Matmul API默认使用MIX模式，即用户从AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消息处理机制会带来额外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直接跳过消息通信框架，完成Matmul计算，提升算子性能。”。
- [多核对齐切分](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/multi_core_aligned_split.md)（`explains`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《多核对齐切分》具体提供“为了实现多核并行，提升计算效率，需要将矩阵数据进行切分，分配到不同的核上进行处理。主要的切分策略有切分K轴和不切分K轴两种。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [EnableMultiCoreSplitK](enable_multi_core_split_k.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《EnableMultiCoreSplitK》具体提供“多核场景，通过该接口开启切K轴。不调用该接口的情况下，默认不切K轴。在GetTiling接口调用前使用。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [GetCoreNum](get_core_num.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetCoreNum》具体提供“获得多核切分所使用的NumBlocks参数。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [GetSingleShape](get_single_shape.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetSingleShape》具体提供“获取计算后的singleCoreM/singleCoreN/singleCoreK。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [GetTiling](get_tiling.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《GetTiling》具体提供“获取Tiling参数。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [SetSplitRange](set_split_range.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《SetSplitRange》具体提供“设置baseM/baseN/baseK的最大值和最小值。目前Tiling暂时不支持该功能。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
- [TCubeTiling结构体](t_cube_tiling_struct.md)（`related`）：《SetDim》的任务是“设置多核Matmul参与运算的核数，区分纯Cube模式和MIX模式的分离与耦合场景”。《TCubeTiling结构体》具体提供“TCubeTiling结构体包含Matmul Tiling切分算法的相关参数，被传递给Matmul Kernel侧，用于Matmul的切块、搬运和计算过程等。TCubeTiling结构体的参数说明见表1。”，它直接用于Matmul 核数、单核形状、split range 与最终 TCubeTiling 的一致性。
<!-- cannbot:related:end -->
