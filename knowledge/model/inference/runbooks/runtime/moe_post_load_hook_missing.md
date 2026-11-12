---
type: Runbook
title: MoE 加载后处理未触发：GroupedMatmul 维度与量化 scale 错误
description: MoE 首次推理 GroupedMatmul Dim 1 mismatch 或 scale 形状错误时，检查权重分片、布局以及 process_weights_after_loading
  后处理调用链。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py
  role: supporting
created_at: '2026-11-09T09:23:45Z'
updated_at: '2026-11-09T12:23:43Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
aliases:
- GroupedMatmul Dim 1 mismatch
- aclnnGroupedMatmul Dim 1 mismatch
---

# MoE 加载后处理未触发：GroupedMatmul 维度与量化 scale 错误

## 症状与探针

首次 Prefill 的 aclnnGroupedMatmul 报 Dim 1 mismatch（来源示例为 2816 与 1408），或量化 scale 形状不匹配。先查看 checkpoint、实际 rank 切片、权重 shape/dtype/stride，再确认 ModelWorker._process_weights_after_loading 是否调用了模型方法，以及模型方法是否分发到相关 quant_method。

## 根因与修复

框架只检查模型是否有 process_weights_after_loading；缺失时不会代替模型做转置、NZ 打包或量化后处理。ForCausalLM 应按本模型规则遍历 quant_method 并执行后处理，且在实际加载结束之后、编图和首次推理之前完成。

不要无条件复制空参数的通用循环：Qwen Dense 的 down_proj.smooth_scales 和若干 weight scale 有 float 适配；Qwen3-MoE 后处理后把 gate 权重转连续；MLA 可能有 kv_b_proj 分拆；LongCat classifier 有转置/NZ 例外。逐项核对 skip 模块、scale dtype、平滑系数、转置、NZ 和融合顺序。不要对已经处理的权重重复执行非幂等转置。

## 验证与回退

保存每个关键模块的加载键、rank 切片和前后布局；在相同实际权重上验证 eager Prefill/Decode，再验证图模式。仅 load_state_dict 成功或修改成连续张量不能证明后处理正确。若维度仍错，回到 shard/融合投影映射，不把所有 GMM 错误归因于该钩子。回退到原始已保存权重及对应加载路径，不能复用被二次变换的参数。

相关：[量化布局](../../optimizations/rules/quant_weight_load_layout_and_naming.md)、[W8A8 scale 链路](../../guides/integration/w8a8_mlp_and_moe_scale_flow.md)、[gate 布局](ge_graph_moe_gate_router_weight_layout.md)。

## Evidence

- [.agents/skills/model-infer-migrator/references/common_issues.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md)
- [executor/core/model_worker/model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)
- [models/qwen/models/modeling_qwen.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen/models/modeling_qwen.py)
- [models/qwen3_moe/models/modeling_qwen3_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py)
