---
type: Guide
title: 中级性能优化
description: 本节在入门功能落地的基础上，介绍Add算子的中级性能优化方法。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 中级性能优化

本节在入门功能落地的基础上，介绍Add算子的中级性能优化方法。
## 性能瓶颈分析
基于入门级代码的Profiling数据（以8192×8192 half为基准），核心性能瓶颈如下：
> 说明：入门功能落地版使用float数据类型是为了简化理解；从中级性能优化版起切换至half数据类型，以获得更高的向量计算性能和搬运效率。以下Profiling数据及优化效果均基于half类型测试。
指标：Case 0（标量基准）：Case 1（单核向量）：Case 2（多核切分）
Task Duration(μs)：1239689.1：6909.6：306.58
aiv_vec_ratio：0：0.11：0.053
aiv_scalar_ratio：0.995：0.033：0.028
aiv_mte2_ratio：0.005：0.873：0.725
aiv_mte3_ratio：0.002：0.378：0.183
核心瓶颈解读：
- 痛点1：标量运算瓶颈（Case 0）：标量指令耗时占比99.5%，逐元素串行执行，无法利用硬件并行能力。
- 痛点2：数据搬运瓶颈（Case 1）：单核向量版本中MTE2占比87.3%，数据搬运成为主要瓶颈，单核搬运请求量不足导致带宽未用满。
- 痛点3：搬运粒度小（Case 2）：多核切分后MTE2占比72.5%，小块搬运（8KB）未充分利用带宽。
## 优化手段解析与实施
### 优化策略1：标量→向量指令
原理解析：标量运算每次只能处理1个数据元素，需要逐元素循环；向量指令（如AscendC::Add）单次可处理多个数据元素，利用向量单元的并行计算能力，可获得百倍以上性能提升。
代码改造点：将for循环配合GetValue/SetValue的标量运算替换为向量API：
性能提升：端到端耗时从1239689.1μs降至6909.6μs，提升99.4%。
### 优化策略2：多核均匀切分 + 大块搬运
原理解析：
- 多核并行：将数据均匀切分到多个AIV Core，实现并行计算。使用均匀切分策略（余数分配到前几个核），确保负载均衡。
- 大块搬运：在UB空间允许范围内增大dataCopyLen，减少搬运次数，摊薄启动开销，更好地利用内存带宽。
代码改造点：
性能提升：Case 2→Case 3，端到端耗时从306.58μs降至268.5μs，减少12.5%。
### 优化策略3：双缓冲流水线并行
原理解析：采用Ping-Pong双缓冲技术，Ping缓冲区进行计算时，Pong缓冲区进行数据搬运，交替执行实现计算与搬运的流水线并行。
代码改造点：
性能提升：Case 3→Case 4，端到端耗时从268.5μs降至264.02μs，减少1.7%。双缓冲的收益有限，说明瓶颈在搬运速度本身。

<!-- cannbot:related:start -->
## 相关

- [VfLoopOptimization](../../../simd_operator_optimization/vector_compute/vf_optimization/vf_loop_optimization.md)（`related`）：中级性能优化 与《VfLoopOptimization》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [优化建议总览表（SIMD算子优化）](../../../simd_operator_optimization/optimization_summary.md)（`related`）：中级性能优化 与《优化建议总览表（SIMD算子优化）》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [基于全局掩码复用的计算性能优化](../../../simd_operator_optimization/vector_compute/mask_reuse_optimization.md)（`related`）：中级性能优化 与《基于全局掩码复用的计算性能优化》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [基础矢量算子](../../../simd_operator_impl/vector_programming/basic_vector_operator.md)（`related`）：《基础矢量算子》说明基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。；《中级性能优化》说明本节在入门功能落地的基础上，介绍Add算子的中级性能优化方法。。二者在基础矢量实现把多核切分、TBuf/TQue、双缓冲、非对齐CopyIn和Add计算串成可执行流程上存在可执行的直接衔接。
- [指令双发优化](../../../simd_operator_optimization/vector_compute/vf_optimization/dual_issue_optimization.md)（`related`）：中级性能优化 与《指令双发优化》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [入门功能落地](getting_started.md)（`same_topic`）：中级性能优化 与《入门功能落地》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [高阶性能打磨](advanced_optimization.md)（`same_topic`）：中级性能优化 与《高阶性能打磨》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
<!-- cannbot:related:end -->
