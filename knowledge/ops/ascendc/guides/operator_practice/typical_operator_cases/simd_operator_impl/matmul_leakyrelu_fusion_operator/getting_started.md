---
type: Guide
title: 入门功能落地
description: 本节以Matmul+LeakyRelu融合算子为例，介绍基于Ascend C编程模型实现Cube-Vector融合计算的基本方法，帮助开发者快速入门融合算子开发。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/getting_started.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 入门功能落地

本节以Matmul+LeakyRelu融合算子为例，介绍基于Ascend C编程模型实现Cube-Vector融合计算的基本方法，帮助开发者快速入门融合算子开发。
## 算子概述
Matmul+LeakyRelu融合计算公式：

- A为左矩阵，形状为[M, K]，数据类型为half；B为右矩阵，形状为[K, N]，数据类型为half
- C为输出矩阵，形状为[M, N]，数据类型为half
## 算子实现
本样例基于C++ Tensor编程模式实现Matmul和LeakyRelu融合计算，展示Cube单元（矩阵计算单元）和Vector单元（向量计算单元）协同计算的编程模式。Cube核完成矩阵乘计算，Vector核完成LeakyRelu激活计算。
数据流路径：
Cube侧：
核间同步与Vector侧：
核函数声明：使用__global__ __mix__(1, 2)声明混合核函数，1个AIC(Cube) + 2个AIV(Vector)组成一个逻辑核，Cube:Vector核数比例为1:2。
完整样例代码请参见Matmul+LeakyRelu入门样例。
## 可优化方向分析
序号：可优化方向：当前实现的问题：预期优化收益
1：L1/L0双缓冲流水线：Cube核内GM→L1→L0A/L0B→L0C→GM各阶段串行执行：Ping-Pong双缓冲使MTE2搬运和MTE1/Mmad计算并行，大幅提升吞吐量
2：Fixpipe与Mmad细粒度并行：Mmad和Fixpipe整块串行：拆分为更小粒度的块，Mmad和Fixpipe交替执行，减少流水线气泡
3：UB双缓冲：Vector核内GM→UB→计算→GM串行执行：UB Ping-Pong双缓冲使MTE2搬运和VEC计算并行
4：Vector核VF融合：当前使用MemBase API，中间结果需写回UB：使用RegBase+asc_vf_call进行VF融合，中间计算在寄存器完成
5：大包搬运：当前仅搬运单块baseM×baseN数据：增大singleCoreM/singleCoreN，减少搬运次数
6：GM中转优化：Cube核结果需经GM中转给Vector核（L0C→GM→UB）：Ascend 950PR支持Fixpipe直接写入UB（L0C→UB），省去GM中转开销

<!-- cannbot:related:start -->
## 相关

- [LeakyRelu](../../../../../apis/simd_api/basic_api/reg_vector_compute/basic_arithmetic/leaky_relu.md)（`explains`）：LeakyRelu 与《入门功能落地》的实质衔接是：Reg LeakyRelu 与 Memory/C Reg/C Vector 入口实现同一负半轴 slope 计算，Matmul-LeakyRelu 案例给出该接口在融合算子中的真实落点。
- [融合算子编程基础知识](../../../simd_operator_impl/fusion_operator_programming/cv_fusion/basics.md)（`related`）：《融合算子编程基础知识》处理“>学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。”。《入门功能落地》明确“本节以Matmul+LeakyRelu融合算子为例，介绍基于Ascend C编程模型实现Cube-Vector融合计算的基本方法，帮助开发者快速入门融合算子开发。”，可直接用于核对CV 融合的数据依赖、Cube/AIV 协作、耦合模式与异步处理编程范式。
- [中级性能优化](intermediate_optimization.md)（`same_topic`）：中级性能优化 与《入门功能落地》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [融合算子编程算子实现](../../../simd_operator_impl/fusion_operator_programming/cv_fusion/operator_impl.md)（`same_topic`）：两卡都以 Matmul+LeakyRelu 实现 Cube-Vector 融合；候选进一步给出 __mix__(1,2)、核间同步和后续优化入口。
- [高阶极限打磨](extreme_optimization.md)（`same_topic`）：高阶章节在中级结果上继续做极限优化，覆盖入门卡末尾列出的 RegBase/VF 融合和搬运优化方向。
<!-- cannbot:related:end -->
