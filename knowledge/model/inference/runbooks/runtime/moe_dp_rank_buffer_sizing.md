---
type: Runbook
title: 多 DP MoE row_idx_decode 形状不匹配：本地 batch 与图模式
description: DP buffer、row_idx_decode 或 npu_moe_compute_expert_tokens / npu_moe_init_routing 报 shape 错时，核对 MoE 本地 batch、batch_size_per_dp_rank、topk 和实际 token 数；覆盖 eager/图模式差异。
tags:
- task.debugging
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: supporting
created_at: '2026-11-09T09:23:45Z'
updated_at: '2026-11-10T02:07:55Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
aliases:
- row_idx_decode shape mismatch
- 多 DP 路由缓存尺寸
- DP buffer
- DP batch buffer
- 多 DP buffer 长度越界
- npu_moe_compute_expert_tokens
- npu_moe_init_routing
---

# 多 DP MoE row_idx_decode 形状不匹配：本地 batch 与图模式

## 症状与快速检查

开启 Attention DP 的 MoE 在 eager 能执行，切到 ge_graph 后 aclnnMoeInitRouting 报 row_idx shape mismatch。记录全局 scheduler_config.batch_size、attn_dp_size、batch_size_per_dp_rank，以及当前 rank 实际输入 token 数、topk 和 row_idx_decode 的形状。

`npu_moe_init_routing` / `npu_moe_compute_expert_tokens` 报 shape 错时，也先核对同一条本地 token 与 per-rank buffer 链路；算子名称只是定位入口，不证明所有同名报错都由 DP 尺寸导致。

## 根因与修复

旧接入模板把全局 batch_size 用于预分配每 rank 的 row_idx_decode / expert_count 等 buffer，实际 rank 只处理自己的请求。在固定的单 token Decode 分支，应使用框架推导的 batch_size_per_dp_rank，结合算子所需的 topk 维度构造 buffer，避免再次除以 DP 度。

batch_size_per_dp_rank 是请求数，不是所有阶段的 token 数。MTP q_len>1、packed 变长 Prefill、静态 batch padding 或 CP 下，需继续按该分支实际 token 范围与算子契约分配，不能机械替换所有全局 batch。expert_count 的专家维也独立于 batch。

## 验证、回退与边界

覆盖多个 DP 度与实际 batch，先验证 eager 再编图；对每个 rank 检查 row_idx 与路由输入的对应关系、输出及通信次数。eager 正常只是线索，不证明唯一根因。失败时恢复已验证的 DP 配置并保留形状探针。

参见 [全局与本地 batch](../../concepts/techniques/inference_config.md)、[packed 边界](../../concepts/techniques/packed_sequence_metadata.md)。

## Evidence

- [.agents/skills/model-infer-migrator/references/common_issues.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-migrator/references/common_issues.md)
- [executor/core/config/inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)
