---
type: Optimization
title: 已归并：SuperKernel 分段与关闭门控
description: 旧分段规则保留历史引用；优化范围选择统一到 SuperKernel 决策，Qwen3-MoE/SGLang 细节进入独立案例，撤下只能分段与零开销的泛化表述。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.graph_execution
status: deprecated
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/patches/0009-feat-support-superkernel.diff
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T13:54:05Z'
platforms:
- a3
replaced_by: model/inference/optimizations/rules/superkernel_decode_ge_graph_fusion_scope
---

# 已归并：SuperKernel 分段与关闭门控

本卡与 SuperKernel 决策重叠，现保留迁移后的历史引用入口，不再独立维护一套融合范围规则。

- 适用条件、范围选择、风险与验证，见[SuperKernel 决策](superkernel_decode_ge_graph_fusion_scope.md)。
- 固定 patch 的 attention/MoE 标记、整层入口与空上下文细节，见[Qwen3-MoE 案例](../cases/qwen3_moe_a3_superkernel_scopes.md)。

原文“只能按功能段”和“关闭态零开销”缺少证据，已撤下。归并不意味着固定 patch 的所有入口都已运行验证，也不扩大到 A3 以外的平台。
