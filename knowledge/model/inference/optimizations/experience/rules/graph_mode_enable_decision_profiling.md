---
type: Optimization
title: 是否/何时启用图模式：按 host 下发占比与 profiling 决策（freetime / host gap / 动态 shape）
description: 图模式收益 ∝ 单 step 内 host 下发 freetime（算子下发调度间隙）占比。先 profile freetime 再决定是否上图模式。 freetime 低的典型场景：视频/图像生成 DiT——每 step 计算量大、host 下发相对占比小，图模式能压的空间有限。观测实例（Atlas A2）单 step freetime 占比 720P 约 0.1%、480P 约 0.5%（仓自报），据此判定收益低、暂不使能图模式，把优化预算投到融合算子 + 序列/VAE 并行上（走 eager set_compile_mode(jit_compile=False)）。 反向场景：decode 密集、host 下发占比高的 LLM 自回归推理，图模式往往有实收益——按各自 freetime 占比另行评估，不套用"DiT 不上图"结论。不可外推为"图模式对所有昇腾推理都无益"。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/33
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/11
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/348
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 是否/何时启用图模式：按 host 下发占比与 profiling 决策（freetime / host gap / 动态 shape）

## 适用场景

在决定"某 workload / 某模块 / 某阶段要不要付图模式（[npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md)）的适配成本"之前——**图模式的主要收益来自压掉 host 侧算子下发的调度间隙**，收益 ∝ host 下发占比。别对所有昇腾推理场景默认使能，也别只信一个粗指标。三条判据：

## 判据 1：先 profile 单 step 的 host freetime 占比，低则跳过

- 图模式收益 ∝ 单 step 内 host 下发 freetime（算子下发调度间隙）占比。**先 profile freetime 再决定是否上图模式**。
- freetime 低的典型场景：视频/图像生成 [DiT](../../../concepts/modules/dit.md)——每 step 计算量大、host 下发相对占比小，图模式能压的空间有限。观测实例（Atlas A2）单 step freetime 占比 720P 约 0.1%、480P 约 0.5%（仓自报），据此判定收益低、暂不使能图模式，把优化预算投到融合算子 + 序列/VAE 并行上（走 eager `set_compile_mode(jit_compile=False)`）。
- 反向场景：decode 密集、host 下发占比高的 LLM 自回归推理，图模式往往有实收益——按各自 freetime 占比另行评估，不套用"DiT 不上图"结论。**不可外推为"图模式对所有昇腾推理都无益"**。

## 判据 2：device profiler NPU kernel 占比 ≠ 是否入图，用 wall-clock host gap

- **陷阱**：某模块 device profiler NPU kernel 占比很小（<5%），据此判"非瓶颈、可保留 eager"——但若该模块一次 forward 触发**大量小 op（含集合通信）**，其 host dispatch 开销全部**不在 device profiler 视野内**。
- **优先动作**：不要只信 device profiler。在推理主循环里加 `torch.npu.synchronize() + time.time()` 分段计时，实测 host vs device 占比；若 wall-clock 明显大于 NPU active 时间（host gap 大），把该模块也纳入图编译。
- 观测实例：某 embedding 模块 device 占比 <5% 却含 ~11 ms host dispatch（一次 forward ~200 个小 op：查表 + all_reduce + shift/where）；把它纳入图后 A2 decode 18.5→7.14 ms（−61%）、A3 12.0→5.86 ms（−51%），减少量 ≈ host dispatch 开销、跨硬件均有效（仓自报）。

## 判据 3：动态 shape 场景默认 eager，prefill 入图靠 profiling

- **动态 shape / double-routing MoE 路径默认 eager**：这类路径算子输入输出多为动态 shape，即使入图也是动态图；**动态 shape 入图并不解决 eager 的下发（dispatch）bound**，只增加图融合能力，而这些融合大多可通过直接调用对应融合算子达到同等效果（维护者确认）。
- **prefill 是否入图 → 看 profiling**：不拍脑袋，先 profiling；仅当观察到下发/调度 bound 且确认入图有收益再使能。prefill 序列不特别短时一般无调度 bound，通常不入图。

## 决策小结

图模式该不该上，永远回到"这个 workload / 模块 / 阶段的 host 下发占比是多少"这一 profile 结果：freetime/host gap 高 → 值得付图适配成本（decode 密集 LLM、host-bound 多小 op 模块）；freetime 低（计算密集 DiT）/ 纯动态 shape → eager + 融合算子 + 并行更划算。图适配的具体工作见 [graph-break-elimination-host-sync-unsupported-ops](../../../guides/experience/interventions/graph_break_elimination_host_sync_unsupported_ops.md) / [graph-mode-decode-only-compile-backends](graph_mode_decode_only_compile_backends.md)。

## 参考实现及其约束

参考实现/证据：Wan2.2-I2V（Atlas A2，DiT，freetime 0.1%/0.5% → eager）、DeepSeek-V3.2-Exp 的 `moe_infer_double_routing`（docstring `only support eager mode`）+ 维护者关于动态 shape/prefill 入图的答复、LongCat-Flash-Lite `NgramEmbedding`（wall-clock host gap 判据 + 跨 A2/A3 复现）。freetime/host gap 数字为仓自报（无独立复测）；`input seq<128` 阈值为社区评论、非维护者确认、不作事实；判据本身（收益 ∝ host 下发占比、用 wall-clock host gap 而非 device kernel%、动态 shape 默认 eager）脱离本模型仍成立。

## 相关经验
- [Ascend 310P 不支持图模式：aclgraph capture 抛 ACL_MODE](../../../runbooks/runtime/ascend_310p_graph_mode_unsupported_enforce_eager.md)

## Evidence

- diff 事实 + 维护者确认（Wan2.2-I2V 昇腾适配）：`set_compile_mode(jit_compile=False)` 以 eager 运行、不使能图模式；freetime 0.1%(720P)/0.5%(480P) 为 RFC 作者自报（doc 披露、无独立复现）。溯源下探 [cann-recipes-infer-issue-33-rfc-wan2-2-i2v-model-inference-support](https://gitcode.com/cann/cann-recipes-infer/issues/33)
- diff 事实（docstring @2c45117）+ 维护者确认：double-routing 只支持 eager；动态 shape 入图不治下发 bound、只加图融合；prefill 入图靠 profiling / 序列不短时不入图。溯源下探 [cann-recipes-infer-issue-11-question-prefill-moe-moe-infer-double-routing](https://gitcode.com/cann/cann-recipes-infer/issues/11)
- diff 事实（结构）+ 仓自报数值（@8fd8db72）：NgramEmbedding device <5% 却 ~11 ms host dispatch，入图后 A2 18.5→7.14 ms；"device profiler <5% ≠ 非热点"结论来自 optimization_report。溯源下探 [cann-recipes-infer-pr-348-feat-add-longcat-flash-lite-model-optimized-by-agent-skills](https://gitcode.com/cann/cann-recipes-infer/merge_requests/348)
