---
type: Concept
title: MoE 专家并行（Expert Parallel / EP）：Prefill 与 Decode 的专家切分和通信
description: EP 将 MoE 专家分布到多个 Rank，通过 dispatch/combine 分发和收回 token；不以 MLA 为前提，Attention 结构及其 TP/DP 是独立维度。说明 Prefill、Decode 的已知部署方案及与 TP 的分工；吞吐和时延仍取决于负载均衡、通信与具体实现，不能仅由启用 EP 推定收益。
aliases:
- Expert Parallel
- EP
tags:
- task.design
- topic.parallelism
- topic.mixture_of_experts
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- agnostic
---

# MoE 专家并行（Expert Parallel / EP）

## Summary

将 MoE（Mixture of Experts）模型的专家分布到不同的卡上，每张卡负责一部分专家的计算。适用于参数规模大但每个 token 只激活部分专家的 MoE 架构。

EP 的前提是 MoE 专家结构，不是 MLA Attention。Qwen3-Next、Gemma-4 等非 MLA 模型也有 Decode EP 实例，见下方固定部署；不能将 MLA 优化的适用条件套到 EP。Attention DP 只复制相应模块，而路由专家仍按 EP 分布，内存预算见[数据并行](data_parallel.md)。

## Mechanism

- 专家权重按组分布到不同 Rank
- dispatch/combine 路径在 Router 计算后通过 AllToAll 类通信将 token 分发到目标专家 Rank
- 该路径专家计算后再经 AllToAll 类通信收回结果；有些实现也可汇总本地专家贡献，但当前Gemma4已删除旧local_experts分支，不能把该策略作为它的配置项
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
- 按阶段核对通信路径：Prefill 可用 Double Routing，Decode 的固定实现多采用融合 dispatch/combine；不能把一种路由路径当作所有阶段的必要条件

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（supporting）
- [deepseek_r1_decode_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md)（supporting）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md)（supporting）
- [optimization_report_ep.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md)（supporting）

## Known Deployments

- **Qwen3-Next Decode**（[qwen3-next](../models/qwen3_next.md)）：`--moe-a2a-backend deepep --deepep-mode auto`，典型 ep_size=16（16die）。配合 [moe-multi-stream](../techniques/moe_multi_stream.md) 将 shared expert 与 dispatch/combine AllToAll 重叠。A8 量化下 dispatch 切换为 `DEEP_NORMAL_MODE_USE_INT8_QUANT=1`。
- **DeepSeek-R1 Prefill**（[deepseek-r1](../models/deepseek_r1.md)）：MoE-EP32。采用 [double-routing](../techniques/double_routing.md)：每卡 两轮路由与顺序恢复，末轮调用一次 npu_moe_finalize_routing，负载相对均匀时，相比 AllGather 方案峰值显存更低、通信量更小。核心融合算子 `npu_moe_init_routing_v2` / `npu_moe_re_routing` / `npu_moe_finalize_routing` + `dist.all_to_all_single`。
- **DeepSeek-R1 Decode**（大 EP 128）：`decode_r1_rank_128_128ep_a8w8c8_mtp*.yaml`，每卡 256/128=2 个 routed expert + 1 个 shared expert。使用一体化算子 `npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（见 [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)），专家计算走 `npu_grouped_matmul`（支持 A8 pertoken_scale）；注意 `HCCL_BUFFSIZE` 配置。可开 `HCCL_OP_EXPANSION_MODE=AIV`（利用 Device Vector Core 加速集合通信）进一步压缩通信时延。
- **Gemma4 EP Decode**：当前用独立MC2通信组和fullmesh_v2，旧mc2/local_experts开关已删除；Prefill保留DR。见[模型](../models/gemma4_26b_a4b.md)。
- **Hy3**：当前已迁models/hy3，MTP1与950FP8/MXFP4路径具有不同通信量化和SP配置；不能沿用旧“GE走MC2/eager固定手工AllToAll”的概括。见[当前Guide](../../guides/models/hy3_preview_deployment.md)。
- **LongCat-Lite**：EP8可每rank持32个路由专家，identity专家不按路由权重EP切分；当前A2每rank专家>24时自动回退DR，不再要求手动关开关。当前MC2代码同时设置fullmesh_v2和copy_expert_num，算子兼容仍需按实际包核验。

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
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（当前EP Decode使用MC2）
- [hy3-preview](../models/hy3_preview.md)（EP=16，12 experts/rank；moe_tp_size=1）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（EP/identity专家、A2自动回退边界）
- [cann-shmem](../techniques/cann_shmem.md)（MoE dispatch&combine 基于对称内存的 win 区 + put/signal/wait 语义）
- [shmem-dispatch-combine](../techniques/shmem_dispatch_combine.md)（DeepEP dispatch&combine 的 SHMEM 重写：发/等状态 + win 拷贝四步范式，三路实现样例）
- [fsdp](../../../training/concepts/parallelism/fsdp.md)（跨域·训练：FSDP2 在 EP 之外对专家二次分片（efsdp mesh））
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 5D 并行枢纽，EP64 路由专家 TP extend EP 走纯 EP、共享专家退化为普通 TP）
- [train-rollout-switch](../../../training/concepts/techniques/train_rollout_switch.md)（跨域·训练：RL reshard 专家参数 AlltoAllV 定向迁移）
- [eplb](../../../training/concepts/techniques/eplb.md)（跨域·训练：MoE EP 专家负载均衡器 EPLB）
