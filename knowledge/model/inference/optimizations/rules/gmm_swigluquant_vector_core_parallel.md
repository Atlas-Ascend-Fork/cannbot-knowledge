---
type: Optimization
title: GMM A8W4 与 SwiGLUQuant 并流：核对 Vector 核占用
description: 针对 MoE FFN 的这对算子，维护者说明 GMM 使用 Vector 核但未占满，仍可与 SwiGLUQuant 并行；不能只凭 mix 类型判定资源冲突，其他算子对及收益需另行剖析。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.precision
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/189
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-23T03:56:00Z'
platforms:
- agnostic
---

# GMM A8W4 与 SwiGLUQuant 并流：核对 Vector 核占用

## 适用场景

在 MoE FFN 上做多流并行调度、要判断「GMM 与 swigluquant 这一对算子能不能并行」时。常见误判：GMM 是 A8W4 的 **mix 算子**、会调用 vector 核，因此和纯 vector 的 swigluquant「并不能并行」——这个误判把「mix 算子会触及 vector 核」直接等同于「占满 vector 核 → 阻塞其它 vector 算子」，是错误前提。

## 核心规则

判断两算子能否并流的依据是**「vector 核是否被占满」，而不是「两算子是否都触及 vector 核」**：

- MoE 的 GMM（grouped matmul，A8W4 = int8 激活 / int4 权重的 mix 算子）计算**集中在 cube 核**，执行中会**同时调用 vector 核**，但**没有占满 vector 核**；
- swigluquant（SwiGLU 激活 + 量化，纯 vector 算子）在 vector 核；
- 两者都没占满 vector 核，留有空档让纯 vector 算子插入 → **可以并行计算**。

上述部分占用判断来自维护者对这对算子的答复。不应因为「GMM 是 mix 算子、会用 vector 核」就直接排除并流；目标实现仍需确认数据依赖、调度与实际核占用，不能把该答复当作任意 GMM 配置都能重叠的保证。

## 何时不适用 / 迁移边界

- 证据仅覆盖 GMM(A8W4) + swigluquant 这一对算子；「cube 主导 mix 算子只部分占用 vector 核」的一般化机制按维护者所述陈述，未跨其它算子对独立验证。迁移到别的算子对时，须按**实际算子的核占用率**判断能否并流，而不是套用本结论。
- 源未给量化的加速数字（无 before→after benchmark），证据只支持「可并行性的判据」，不支持推断收益幅度。
- 关联：MoE 多流重叠的具体落法见 [moe-shared-expert-decode-dual-stream](moe_shared_expert_decode_dual_stream.md)；多流后分核再平衡见 [moe-multi-stream-limit-core-num](decode_multi_stream_overlap_core_balance.md)。

## Evidence

- 「GMM 集中在 cube 核 / 执行中同时调用 vector 核 / swigluquant 在 vector 核 / 两者未占满 vector 核 → 可并行」：维护者确认（官方在 issue 讨论区逐字答复，该 issue 标 Accepted）。该事件无关联 PR / 无 diff；「未占满 vector 核」为维护者技术判断、未独立 profile 复测。溯源下探 [cann-recipes-infer-issue-189-bug-report-deepseekv4](https://gitcode.com/cann/cann-recipes-infer/issues/189)。
