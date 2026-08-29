---
type: Optimization
title: 判断两算子能否多流并行看 vector 核是否被占满：cube 主导的 mix 算子（GMM）只部分占用、可与纯 vector 算子（swigluquant）并行
description: 判断两算子能否多流并行看 vector 核是否被占满：cube 主导的 mix 算子（GMM）只部分占用、可与纯 vector 算子（swigluquant）并行。在 MoE FFN 上做多流并行调度、要判断「GMM 与 swigluquant 这一对算子能不能并行」时。常见误判：GMM 是 A8W4 的 mix 算子、会调用 vector 核，因此和纯 vector 的 swigluquant「并不能并行」——这个误判把「mix 算子会触及 vector 核」直接等同于「占满 vector 核 → 阻塞其它 vector 算子」，是错误前提。
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
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 判断两算子能否多流并行看 vector 核是否被占满：cube 主导的 mix 算子（GMM）只部分占用、可与纯 vector 算子（swigluquant）并行

## 适用场景

在 MoE FFN 上做多流并行调度、要判断「GMM 与 swigluquant 这一对算子能不能并行」时。常见误判：GMM 是 A8W4 的 **mix 算子**、会调用 vector 核，因此和纯 vector 的 swigluquant「并不能并行」——这个误判把「mix 算子会触及 vector 核」直接等同于「占满 vector 核 → 阻塞其它 vector 算子」，是错误前提。

## 核心规则

判断两算子能否并流的依据是**「vector 核是否被占满」，而不是「两算子是否都触及 vector 核」**：

- MoE 的 GMM（grouped matmul，A8W4 = int8 激活 / int4 权重的 mix 算子）计算**集中在 cube 核**，执行中会**同时调用 vector 核**，但**没有占满 vector 核**；
- swigluquant（SwiGLU 激活 + 量化，纯 vector 算子）在 vector 核；
- 两者都没占满 vector 核，留有空档让纯 vector 算子插入 → **可以并行计算**。

即 cube 主导的 mix 算子对 vector 核只是**部分占用**而非饱和占用。不应因为「GMM 是 mix 算子、会用 vector 核」就判定它与纯 vector 算子无法并行——这是一条**应保留/采用**的多流并行，而非需要规避的冲突。

## 何时不适用 / 迁移边界

- 证据仅覆盖 GMM(A8W4) + swigluquant 这一对算子；「cube 主导 mix 算子只部分占用 vector 核」的一般化机制按维护者所述陈述，未跨其它算子对独立验证。迁移到别的算子对时，须按**实际算子的核占用率**判断能否并流，而不是套用本结论。
- 源未给量化的加速数字（无 before→after benchmark），本条只沉淀「可并行性的判据」这一判断，不外推收益幅度。
- 关联：MoE 多流重叠的具体落法见 [moe-shared-expert-decode-dual-stream](moe_shared_expert_decode_dual_stream.md)；多流后分核再平衡见 [moe-multi-stream-limit-core-num](../cases/moe_multi_stream_limit_core_num.md)。

## Evidence

- 「GMM 集中在 cube 核 / 执行中同时调用 vector 核 / swigluquant 在 vector 核 / 两者未占满 vector 核 → 可并行」：维护者确认（官方在 issue 讨论区逐字答复，该 issue 标 Accepted）。该事件无关联 PR / 无 diff，不适用「读实际 diff」核门；「未占满 vector 核」为维护者技术判断、未独立 profile 复测。溯源下探 [cann-recipes-infer-issue-189-bug-report-deepseekv4](https://gitcode.com/cann/cann-recipes-infer/issues/189)。

<!-- cannbot:related:start -->
## 相关

- [SwiGluQuant A2/A3 ACLNN 算子知识](../../../../../ops/ascendc/operators/aclnn/nn/quant/swi_glu_quant.md)（`related`）：“单 Kernel `swi_glu_quant`，全部 Host 可达 body 均为 `AIV_VECTOR`；无 Cube/AIC、MIX_CV、SIMT、NDDMA 或 AICPU。”与“swigluquant（SwiGLU 激活 + 量化，纯 vector 算子）在 vector 核；”分别给出双端正文事实；算子卡确认 SwiGluQuant 的全部可达 body 为纯 AIV_VECTOR，优化规则利用这一核类型与 cube 主导 GMM 的剩余 vector 容量判断双流并行，连接实现资源属性与调度决策。
<!-- cannbot:related:end -->
