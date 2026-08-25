---
type: Guide
title: FlashAttention算子性能调优案例
description: 本案例中的算子FlashAttentionScoreGrad，用于训练场景下计算注意力的反向输出，即FlashAttentionScore算子的反向计算。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/best_practices/flash_attention_tuning.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2]
---

# FlashAttention算子性能调优案例

## 案例介绍
本案例中的算子FlashAttentionScoreGrad，用于训练场景下计算注意力的反向输出，即FlashAttentionScore算子的反向计算。
已知注意力的正向计算公式为：
为方便表达，以变量S和P表示计算公式：
则注意力的反向计算公式为：
计算流程图如下：
按照FlashAttention反向计算流程的实现，简介整体计算流程如下。对本算子的算法感兴趣的用户可简单了解，无需重点关注。
1.  重计算p，本步骤重计算了FlashAttention流程中的softmax结果p，计算结果保存在ub中。
2.  计算dp，该计算包含matmul计算和dropout计算，matmul计算中，左矩阵为dy，右矩阵为转置后的value。
3.  计算ds，本计算中，FlashSoftmaxGrad计算的入参为dy、正向输出attention_in，该结果与dp做减操作，最终的结果与p相乘得到结果ds。
4.  计算dq，本计算将ds结果与key做matmul计算，并将结果与scale相乘得到结果dq。
5.  计算dk，本计算将转置后的ds结果与query做matmul计算，并将结果与scale相乘得到结果dk。
6.  计算dv，本计算将p的结果做drop计算，转置后与dy做matmul计算。
本案例的验证平台为Atlas A2 训练系列产品/Atlas A2 推理系列产品，以两个场景为例，第一个场景的输入维度信息为：B=1，N1=12，N2=12，S1=6144，S2=6144，D=128，causal场景，即atten_mask的形状为下三角，如图2。第二个场景的输入维度信息为：B=24，N1=5，N2=5，S1=9216，S2=9216，D=64，不带atten_mask和drop_mask输入。主要涉及的优化手段包括tiling基本块大小调整，核间负载均衡，CV流水并行，MTE2流水优化以及FixPipe流水优化等优化手段。
## 获取性能数据
流水优化分析工具包括CAModel和Profiling工具，分别从两个方面分析：第一个是从Profiling工具生成的Profiling数据中分析各项流水的占比，第二个是从CAModel工具生成的打点图分析各流水并行情况。
## 分析主要瓶颈点
通过观察分析流水图和Profiling数据，结合优化经验来判断性能瓶颈点。在优化过程中不同阶段可能会出现不同的瓶颈点，需要不断优化以达到最佳性能。
-   根据优化经验，循环间会存在一些不必要的性能开销，循环越多性能可能越差；满足UB最大空间限制的情况下，UB切分的基本块越大，循环越少。算子中通过InitBuffer接口分配UB buffer大小。
如上代码所示，InitBuffer接口的第二个参数表示buffer占用的大小，所有buffer大小的和即为占用的总空间。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启MTE2 Preload](matmul_tuning_cases/matmul_mte2_preload.md)（`related`）：Attention 中 QK/PV Matmul 可复用 MTE2 preload 原则。
- [Mix合图包入 V2 致任务数减半 E2E 劣化](../../../runbooks/performance/mix_v2_e2e.md)（`related`）：该卡用端到端 profile 验证 FlashAttention MIX 调度收益。
- [PyPTO F40005 UB 越界：scope 扩展压满 UB](../../../runbooks/compilation/pypto_f40005_ub_scope_ub.md)（`related`）：FlashAttention 变换若造成 UB scope 错误需先修构建，再评性能。
- [unroll s2 内层循环破坏 flash 在线 softmax 循环态](../../../runbooks/precision/unroll_s2_flash_softmax.md)（`related`）：S2 unroll 会改变 softmax 规约顺序和精度，调优需同时验证。
<!-- cannbot:related:end -->
