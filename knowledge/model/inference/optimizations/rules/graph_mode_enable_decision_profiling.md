---
type: Optimization
title: 图模式决策：profiling、host 下发占比与 freetime / host gap
description: 在已有 A2/A3 证据范围内，按 host 下发占比、freetime、host gap 与 profiling 评估是否启用图模式；结合设备时间线、动态 shape、算子支持及精度验收，不从差值直接推导收益。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/11
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/33
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8fd8db72e333d38e15e54b8907a45da6134fa8fc/models/longcat_flash_lite/README.md
  role: constraint
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/8fd8db72e333d38e15e54b8907a45da6134fa8fc/models/longcat_flash_lite/optimization_report.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T06:43:54Z'
platforms:
- a2
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - latency
      - tpot
---

# 图模式决策：profiling、host 下发占比与 freetime / host gap

## 适用场景与信号

本卡集中维护图模式选择，平台范围按已有 A2/A3 证据填写。在决定某个工作负载或模块是否值得入图时，先核对 host 下发、同步等待与设备执行的时间线。Scope 不限定某个图后端或阶段，因为这里讨论的是选择与验收；未声明的维度仍是未知。

## 决策

- 设备 kernel 时间占比低，不代表端到端开销低。对多小算子或集合通信模块，结合同步前后的 wall-clock 与设备时间线排查 host gap。
- host gap 大只是候选信号。同步、通信等待和测量扰动也会造成差值，不能把全部差值直接归因为 Python 下发，或从比例线性推导可获得的加速。
- freetime 很低时，应比较图适配成本与其他优化方向；不从一个视频模型推导所有 DiT 或所有平台都不值得入图。
- 入图前确认算子支持、动态图行为、graph break、缓存更新与输出验收；候选图能编译或性能变快都不能替代正确性检查。

## 动态 shape 与 double-routing

Issue 11 的回复说明：各算子支持入图时，double-routing 本身没有固有的入图禁令；动态 shape 与多次 AllToAllV 仍可能影响收益。另有回复建议这类实践优先考虑 eager 与融合算子。两者分别讨论可行性和代价，不能合成为“动态 shape 一律不能入图”。

某固定源码的 `only support eager mode` 注释只约束该实现，不能升级为框架或算子的通用限制；Prefill 是否值得入图也应按实际负载评估，不设置未经核验的序列长度阈值。

## 实施与证据入口

- [LongCat-Lite A2/A3 NgramEmbedding 入图案例](../cases/longcat_lite_ngram_graph_host_gap.md)：记录图外模块的 host gap、实现变化、自报性能与 token 分歧。
- [Wan2.2 A2 freetime 观测](../benchmark_observations/wan22_a2_graph_mode_freetime.md)：保留低 freetime 下暂不启用图的决策及未提供的对比条件。

图编译与 graph break 的具体实施复用[编译入口](../../guides/optimization/graph_mode_decode_only_compile_backends.md)和[图中断处置](../../guides/integration/graph_break_elimination_host_sync_unsupported_ops.md)。关联 310P 故障卡不构成本规则的 310P 适用证据。

## 验证、风险与回退

固定硬件、软件、模型、量化、负载及其他开关，分别测冷启动和 warmup 后稳态，保存重复次数与波动。按业务要求核对输出、误差或任务精度，明确 token 分歧是否可接受；来源称“语义等价”不代表本次已验收。

若收益不足、重新编译频繁或精度不满足，恢复原执行模式及合法缓存/配置，再验证输出。本文没有运行模型、独立复测数据或增加 `verified`。
