---
type: Optimization
title: 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate
description: 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate。对一个已能在昇腾单卡跑通的模型做推理优化（提性能、不破精度）时，按一条固定分阶段流程推进——每阶段有独立的精度+性能验证 gate，按序不可跳过/不可并行。这给优化 agent 一个可复用的动作序列与验收关口，避免一次性堆改动导致精度/性能问题难定位。
tags:
- task.optimization
- topic.attention
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/328
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 单卡 NPU 推理优化的三阶段固定流程：KVCache 静态化+FA 替换 → torch_npu 融合算子替换 → GE 图模式(仅 decode)，每阶段精度+性能 gate

## 适用场景

对一个已能在昇腾单卡跑通的模型做**推理优化**（提性能、不破精度）时，按一条**固定分阶段流程**推进——每阶段有独立的精度+性能验证 gate，**按序不可跳过/不可并行**。这给优化 agent 一个可复用的动作序列与验收关口，避免一次性堆改动导致精度/性能问题难定位。

## 三阶段（按序、每阶段过 gate 才进下一阶段）

1. **阶段一：KVCache 静态化 + FA 替换**。把 KV cache 改为静态形状、注意力换成昇腾 [FlashAttention 融合算子](../../../concepts/kernels/fused_infer_attention_score.md)。过精度 gate（与基线对齐）+ 性能 gate 后进下一阶段。
2. **阶段二：torch_npu 融合算子替换（Attention 之外）**。把 Attention 以外的原生小算子（norm/rope/激活/matmul 组合等）换成 torch_npu 融合算子。同样过精度+性能 gate。
3. **阶段三：GE 图模式适配（仅 Decode）**。把 decode 路径适配到 [GE 图模式](../../../concepts/techniques/npu_graph_mode.md)（prefill 不做）。过 gate 收尾。

## 为何分阶段 + gate

- 每阶段只引入一类改动，出问题能立刻定位到该阶段；
- 精度 gate 防止某步优化静默破精度被后续阶段掩盖；
- 顺序有依赖（先静态化/FA 才好上融合算子，先融合算子稳定再上图模式），故不可跳过/并行。

## 参考实现

参考 cann-recipes-infer 的 `model-optimize` agent skill——它把上述三阶段流程与每阶段的精度/性能验证固化为可执行的优化脚本序列。

## 风险 / 边界

- 阶段三仅 Decode 适配图模式；prefill 上图模式不在此流程内。
- 这是单卡推理优化流程；多卡并行优化是另一套（并行选型见相关经验）。

## 相关经验

- 注意力换 FIA 的 sparse_mode 细节见 [attention-to-fia-sparse-mode-sink-window](attention_to_fia_sparse_mode_sink_window.md)。
- 多卡并行/平台部署选型见 [ascend-deploy-parallel-variant-and-nondefault-platform](ascend_deploy_parallel_variant_and_nondefault_platform.md)。

## Evidence

- `diff 事实`（@73ed847）：`model-optimize` skill 规定三阶段（KVCache 静态化+FA → torch_npu 融合算子替换 → GE 图模式仅 Decode）、每阶段精度+性能 gate、按序不可跳过/并行。
- 溯源下探：[cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)