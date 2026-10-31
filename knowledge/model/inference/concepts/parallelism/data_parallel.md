---
type: Concept
title: Data Parallel
description: 将不同的请求/batch 分配到不同的模型副本上并行推理的策略，用于提升推理吞吐量。在推理场景中通常以 DP 通信域的形式与 TP/EP 配合使用。
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- a3
---
# Data Parallel

## Summary

将不同的请求/batch 分配到不同的模型副本上并行推理的策略，用于提升推理吞吐量。在推理场景中通常以 DP 通信域的形式与 TP/EP 配合使用。

## Mechanism

- 整模型 DP 的每个副本持有完整模型（或其 TP 切片）；模块级 Attention DP 仅要求 Attention 权重全载，MoE 专家仍可按 EP 分布
- 不同请求路由到不同 DP Rank 独立推理
- 在 SGLang 等框架中，DP 通信域还可被 CP 复用

## Applicable Scenarios

- 高吞吐需求场景，单副本无法满足 QPS 要求
- 多节点部署时通过 DP 扩展吞吐

## Configuration

- DP按目标模块的通信组定义；Attention DP与MoE EP可能覆盖同一rank集合，不能通用套用“总卡数/(TP×EP)”计算独立维度。
- 在 PD 分离部署中，Prefill 和 Decode 可使用不同的 DP 配置

## Constraints

- 内存预算按复制范围计算：整模型 DP 复制模型，Attention DP+MoE EP 仅复制 Attention 等指定模块，不能按每 rank 完整模型估算
- 不减少单请求延迟

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（supporting）

## Known Deployments

- **Qwen3-Next PD 混部**：`--enable-dp-attention --dp-size 8 --tp 16`，DP 通信域在 Attention 层独立。CP 场景下 DP 通信域被 [context-parallel](context_parallel.md) 复用，因此 CP 与 DP 互斥（README 约束 5）。
- **DeepSeek-R1 Prefill / Decode**（[deepseek-r1](../models/deepseek_r1.md)）：主流部署走 **纯 DP MLA**（`attn_tp_size=1`），每卡部署完整 MLA 权重，KVCache 按本卡请求独占、无冗余。该策略在请求量大或 KVCache 占用高的场景下最大化吞吐，但短序列混合批次下存在计算负载不均、请求数不足时 TTFT 拉长的问题——此时改用 [sp-tp-sp](sp_tp_sp.md)。固定示例中的DP128/EP128是并行组规模，不能据此推导128物理卡。MLA-DP 切分下 prefill 通信几乎全部来自 MoE 阶段的 AlltoAll（dispatch/combine），故 MLA-DP + MoE-[expert-parallel](expert_parallel.md) 场景用 micro-batch 双流把计算与 AlltoAll 并行起来、以计算掩盖 dispatch/combine 通信耗时。该固定 MLA-DP + MoE-EP 策略要求使用默认 SDMA，不能开启 HCCL_OP_EXPANSION_MODE=AIV，否则通信与计算争抢资源、时延可能变长；还须确认切分前后计算/通信性能近似线性，且原计算未 host-bound；来源测量见[R1 Prefill 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)。

 DeepSeek-R1 Prefill MLA 纯 DP 切分原貌（请求按卡独立、KV-Cache 无冗余）：

 ![DeepSeek-R1 Attention DP 切分](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/figures/image_attention_dp.png)
 *来源：[`docs/models/deepseek-r1/figures/image_attention_dp.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/figures/image_attention_dp.png)（cann-recipes-infer @ 944d2d3）*

## Links

- [tensor-parallel](tensor_parallel.md)
- [expert-parallel](expert_parallel.md)
- [context-parallel](context_parallel.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [deepseek-r1](../models/deepseek_r1.md)
- [sp-tp-sp](sp_tp_sp.md)
- [deepseek-v4](../models/deepseek_v4.md)（Decode Attention 用 DP，配合 MoE EP + LM_head TP）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（`attn_tp=1` → DP=8；full 层 N_kv=2 致 TP 上限 2，故全用 DP 最大化吞吐）
- [hy3-preview](../models/hy3_preview.md)（16 die `attn_tp_size=4` → Attention DP 体现在 attn_tp 之外的部署面；当前Decode视图为 `attn_dp_size=world_size//attn_tp_size`，CP Prefill另用 `cp_prefill_dp_size=world_size//(attn_tp_size·cp_size)`）
- [fsdp](../../../training/concepts/parallelism/fsdp.md)（跨域·训练：FSDP2 全分片数据并行（ZeRO-3 同源））
