---
type: Guide
title: 单卡推理优化指南：分阶段验证 KV、融合算子与 Decode 图模式
description: 记录来源 model-optimize Skill 的三阶段参考流程：KVCache 与 FA、其他融合算子、Decode 图适配；每阶段对照基线验证，具体阶段是否需要取决于现有实现和瓶颈。
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
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# 单卡推理优化指南：分阶段验证 KV、融合算子与 Decode 图模式

## 适用场景

对一个已能在昇腾单卡跑通的模型做**推理优化**（提性能、不破精度）时，可参考来源 Skill 的分阶段流程推进，每阶段分别验证精度和性能。先检查模型已经完成哪些步骤，再按瓶颈和依赖选择需要的阶段。这给优化 agent 一个可复用的动作序列与验收关口，避免一次性堆改动导致精度/性能问题难定位。

## 来源流程中的三个阶段

1. **阶段一：KVCache 静态化 + FA 替换**。把 KV cache 改为静态形状、注意力换成昇腾 [FlashAttention 融合算子](../../concepts/kernels/fused_infer_attention_score.md)。过精度 gate（与基线对齐）+ 性能 gate 后进下一阶段。
2. **阶段二：torch_npu 融合算子替换（Attention 之外）**。把 Attention 以外的原生小算子（norm/rope/激活/matmul 组合等）换成 torch_npu 融合算子。同样过精度+性能 gate。
3. **阶段三：GE 图模式适配（仅 Decode）**。把 decode 路径适配到 [GE 图模式](../../concepts/techniques/npu_graph_mode.md)（prefill 不做）。过 gate 收尾。

## 为何分阶段 + gate

- 每阶段只引入一类改动，出问题能立刻定位到该阶段；
- 精度 gate 防止某步优化静默破精度被后续阶段掩盖；
- 来源 Skill 采用串行推进以隔离变量；这不是所有模型的必需技术顺序，也不新增仓库强制流程。

## 验证与停止条件

每次变更保存对应输入、权重、软件版本、输出对照和预热后性能。采用该模型既定的精度标准；来源没有给出跨模型通用阈值。某阶段精度不通过或没有净收益时回退该阶段，先定位原因，避免继续叠加无法归因的修改。已满足的阶段可保留现状。

入图取舍统一见 [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)，具体编译步骤见 [Decode 图编译指南](graph_mode_decode_only_compile_backends.md)。

## 参考实现

参考 cann-recipes-infer 的 `model-optimize` agent skill——它把上述三阶段流程与每阶段的精度/性能验证固化为可执行的优化脚本序列。

## 风险 / 边界

- 阶段三仅 Decode 适配图模式；prefill 上图模式不在此流程内。
- 这是单卡推理优化流程；多卡并行优化是另一套（并行选型见相关经验）。

## 相关经验

- 注意力换 FIA 的 sparse_mode 细节见 [attention-to-fia-sparse-mode-sink-window](../../optimizations/rules/attention_to_fia_sparse_mode_sink_window.md)。
- 多卡并行/平台部署选型见 [ascend-deploy-parallel-variant-and-nondefault-platform](../../optimizations/rules/ascend_deploy_parallel_variant_and_nondefault_platform.md)。

## Evidence

- `diff 事实`（@73ed847）：`model-optimize` skill 规定三阶段（KVCache 静态化+FA → torch_npu 融合算子替换 → GE 图模式仅 Decode）、每阶段精度+性能 gate、按序不可跳过/并行。
- 溯源下探：[cann-recipes-infer-pr-328-feat-add-agent-optimization-skills-and-evaluation-reports](https://gitcode.com/cann/cann-recipes-infer/merge_requests/328)