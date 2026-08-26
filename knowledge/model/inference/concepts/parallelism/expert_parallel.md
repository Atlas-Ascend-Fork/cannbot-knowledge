---
type: Concept
title: Expert Parallel
description: 将 MoE（Mixture of Experts）模型的专家分布到不同的卡上，每张卡负责一部分专家的计算。适用于参数规模大但每个 token 只激活部分专家的 MoE 架构。
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-r1/deepseek_r1_prefill_optimization.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Expert Parallel

## Summary

将 MoE（Mixture of Experts）模型的专家分布到不同的卡上，每张卡负责一部分专家的计算。适用于参数规模大但每个 token 只激活部分专家的 MoE 架构。

## Mechanism

- 专家权重按组分布到不同 Rank
- Router 计算后通过 AllToAll 通信将 token 分发到目标专家所在 Rank
- 专家计算完成后通过 AllToAll 通信将结果收集回来
- 通常配合 TP 使用（EP 切 MoE 层，TP 切 Attention 层）

## Applicable Scenarios

- MoE 架构模型（DeepSeek-R1、DeepSeek-V3.2-Exp、Qwen3-MoE、Qwen3-Next 等）
- Decode 阶段尤其适用（每个 token 只激活少量专家）

## Configuration

- EP size 通常等于节点卡数（如 8EP）或更大
- 与 TP 的配合：如 Qwen3-Next decode 阶段使用 EP+TP 混合

## Constraints

- AllToAll 通信开销是主要瓶颈
- 负载均衡依赖 Router 的质量
- 需配合 Double Routing 等技术优化通信效率

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — MoE 模型普遍使用 EP 策略

## Known Deployments

- **Qwen3-Next Decode**（[qwen3-next](../models/qwen3_next.md)）：`--moe-a2a-backend deepep --deepep-mode auto`，典型 ep_size=16（16die）。配合 [moe-multi-stream](../techniques/moe_multi_stream.md) 将 shared expert 与 dispatch/combine AllToAll 重叠。A8 量化下 dispatch 切换为 `DEEP_NORMAL_MODE_USE_INT8_QUANT=1`。
- **DeepSeek-R1 Prefill**（[deepseek-r1](../models/deepseek_r1.md)）：MoE-EP32。采用 [double-routing](../techniques/double_routing.md)：每卡 2 次 init-routing + 2 次 finalize-routing，相比 AllGather 方案峰值显存更低、通信量更小。核心融合算子 `npu_moe_init_routing_v2` / `npu_moe_re_routing` / `npu_moe_finalize_routing` + `dist.all_to_all_single`。
- **DeepSeek-R1 Decode**（大 EP 128）：`decode_r1_rank_128_128ep_a8w8c8_mtp*.yaml`，每卡 256/128=2 个 routed expert + 1 个 shared expert。使用一体化算子 `npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（见 [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)），专家计算走 `npu_grouped_matmul`（支持 A8 pertoken_scale）；注意 `HCCL_BUFFSIZE` 配置。可开 `HCCL_OP_EXPANSION_MODE=AIV`（利用 Device Vector Core 加速集合通信）进一步压缩通信时延。
- **Gemma-4-26B-A4B Decode**（[gemma4-26b-a4b](../models/gemma4_26b_a4b.md)）：EP=8，128 experts / 8 = 16 experts/rank。Decode 在 `mc2`（[moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)）与 `local_experts`（每 rank 算全部本地 expert + 末次 AllReduce、对 ge_graph fullgraph 友好）两路径间按 `experts_per_rank ≤ 24` 自动切换。
- **Hy3-preview Decode**（[hy3-preview](../models/hy3_preview.md)）：`moe_ep_size=16`（全卡 EP），192 experts / 16 = 12 experts/rank；`moe_tp_size=1`（expert intermediate=1536 太小，TP 会切碎矩阵）。ge_graph 下走 MC2 dispatch/combine（[moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)）替代手动 all_to_all，eager 下走手动 all_to_all。
- **LongCat-Flash-Lite EP**（[longcat-flash-lite](../models/longcat_flash_lite.md)）：`moe_ep=8`、`moe_tp=1`，256 routed / 8 = 32 routed expert/rank + 128 zero/identity expert（每卡持有，不参与 EP 切分）；attn_tp=4 + attn_dp=2、dense MLP DP-replicated、ngram 子表独立 TP=8。Decode 走 MC2 dispatch/combine（[moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)），Prefill 走 [double-routing](../techniques/double_routing.md)；A2 因 `experts_per_rank ≤ 24`（32/rank 不满足）回退 double-routing 或 eager。

## Links

- [tensor-parallel](tensor_parallel.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [deepseek-r1](../models/deepseek_r1.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [double-routing](../techniques/double_routing.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)（Decode 路径用的一体化融合算子，与 EP 部署分工）
- [prefill-micro-batch](../techniques/prefill_micro_batch.md)
- [inference-config](../techniques/inference_config.md)
- [deepseek-v4](../models/deepseek_v4.md)（Decode MoE 用 EP，配合 Attention DP）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（EP=8，16 experts/rank；mc2 / local_experts 双路径）
- [hy3-preview](../models/hy3_preview.md)（EP=16，12 experts/rank；moe_tp_size=1）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（EP=8，32 routed + 128 zero expert/rank；A2 experts_per_rank≤24 回退 double-routing）
- [cann-shmem](../techniques/cann_shmem.md)（MoE dispatch&combine 基于对称内存的 win 区 + put/signal/wait 语义）
- [shmem-dispatch-combine](../techniques/shmem_dispatch_combine.md)（DeepEP dispatch&combine 的 SHMEM 重写：发/等状态 + win 拷贝四步范式，三路实现样例）
- [fsdp](../../../training/concepts/parallelism/fsdp.md)（跨域·训练：FSDP2 在 EP 之外对专家二次分片（efsdp mesh））
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 5D 并行枢纽，EP64 路由专家 TP extend EP 走纯 EP、共享专家退化为普通 TP）
- [train-rollout-switch](../../../training/concepts/techniques/train_rollout_switch.md)（跨域·训练：RL reshard 专家参数 AlltoAllV 定向迁移）
- [eplb](../../../training/concepts/techniques/eplb.md)（跨域·训练：MoE EP 专家负载均衡器 EPLB）
