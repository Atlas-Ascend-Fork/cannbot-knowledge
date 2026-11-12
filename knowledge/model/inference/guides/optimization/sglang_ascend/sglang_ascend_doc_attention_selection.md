---
type: Guide
title: SGLang 昇腾 attention 后端与混合 GDN 的选择边界
description: 区分 full attention、MLA、GDN 和多模态接口，保留新旧支持表与页大小/树候选冲突。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/attention_backend.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/breakable_cuda_graph.mdx
  role: constraint
- resource: https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/attention_backend.mdx
  role: primary
created_at: '2026-11-08T12:09:58Z'
updated_at: '2026-11-08T12:09:58Z'
platforms: []
---

# SGLang 昇腾 attention 后端与混合 GDN 的选择边界

## 分开选择不同层的后端

NPU普通attention选ascend，多模态另由mm-attention-backend选择ascend_attn；对应家族有多模态实现不等于任意模型已完整适配。Hybrid GDN模型仍需普通full-attention后端，当前文档限定NPU full attention为ascend。GDN线性层由架构自动启用，不能用attention-backend选择GDN；线性层另有linear-attn-backend及prefill/decode覆盖。

当前GDN表将NPU Triton列为prefill/decode支持、MTP verify不支持；但同快照Qwen3.5/3.6/Next教程明确使用NEXTN。这是文档表与模型路径的冲突，不能据单行推导全部MTP能力。来源没有具体芯片范围，本卡draft空platforms。

## 读取表格时保留版本差异

普通Ascend行在旧表中spec topk1、topk>1等列为不支持，新表部分列变为支持；MLA行两版仍写page128并对额外能力多标不支持。不能把普通attention的新增勾选借给MLA、GDN或任意芯片。请求sampling top_k与draft分支eagle-topk不是同一维度；树形候选还需draft与verify路径同时支持。

通用页把Ascend native page size写128；当前GLM5.3-Flash的950配方却用page64。应按具体模型/backend实现核对，不能将128提升成所有950路径的硬限制。完整页才可复用prefix cache，尾部不足一页不参与该完整页匹配；这也不意味着其token被从请求中删除。增大页可能降低可复用前缀粒度，不能仅依据kernel吞吐选页大小。

## 图调试的负向边界

breakable CUDA graph文档明确只支持CUDA/ROCm，NPU上的debug-cuda-graph会自动禁用并警告。这与NPU自身decode graph、ViT graph或其他piecewise实现是不同入口；不能因参数中保留CUDA名称就假定该调试工具能在NPU运行。实际兼容、质量和性能仍应按模型与版本验证，本次未执行设备测试。

## Evidence

- [sglang：docs/docs/advanced_features/attention_backend.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/attention_backend.mdx)（primary）
- [sglang：docs/docs/advanced_features/breakable_cuda_graph.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/advanced_features/breakable_cuda_graph.mdx)（constraint）
- [sgl_docs：docs/advanced_features/attention_backend.mdx](https://github.com/sgl-project/sgl-docs/blob/c27f107bf92712760cff32fdd3c1cf08d2372b1a/docs/advanced_features/attention_backend.mdx)（primary）
