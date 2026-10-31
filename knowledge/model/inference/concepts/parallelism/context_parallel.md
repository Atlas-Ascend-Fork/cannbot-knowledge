---
type: Concept
title: 上下文并行（Context Parallel / CP）：长上下文 Prefill 的序列切分
description: CP 沿 Sequence 维度切分长上下文 Prefill 的计算，降低单 Rank 的激活值压力。区分 Qwen3-Next 的 CP+TP 与其他整域 CP 实现；通信域、KV 汇聚及 PD 分离限制按具体案例核对。
aliases:
- Context Parallel
- CP
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/sgl_kernel_npu_support_gdn_cp.patch
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a3
---

# 上下文并行（Context Parallel / CP）

## Summary

将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。

## Mechanism

CP 的共同点是沿序列拆分计算；交换方式由实现决定。以下为固定 Qwen3-Next/SGLang **CP+TP** 路径：

- 每个 Rank 处理自己的 Sequence chunk；KV 在 CP 组 AllGather。
- 本地 Q chunk 与汇聚的 KV 计算 Attention。
- 输出在 **TP 组** ReduceScatter，以完成该实现的 TP 布局转换。
- 该路径复用 DP 通信域且有 PD 分离限制；不是其他 CP 实现的共同要求。

## Applicable Scenarios

- Prefill 阶段的长序列处理（64K+ tokens）
- Attention 计算量 O(S²) 使得长序列下单卡 OOM 风险高
- 适用于标准 Attention 和 GatedAttention 等结构

## Configuration

以下具体接口约束来自固定 Qwen3-Next/SGLang 路径，不是 Context Parallel 的通用限制；其他模型按各自案例选择通信域和切分。

- 启动参数 cp_size < tp_size 且 tp_size % cp_size == 0（CP 仅 PD 分离场景可开，P/D 卡数须相同；复用 DP 通信域故与 DP 互斥）
- 典型配置如 mCP * nTP（如 CP4 * 局部 TP2，对应整体 tp_size=8）
- 需配合 ZigZag 负载均衡解决因果注意力的计算不均

## Constraints

- Qwen3-Next/SGLang 的固定接口要求 `cp_size < tp_size`，且整体 tp_size 须被 cp_size 整除；该路径只在 P/D 卡数相同的 PD 分离模式启用（SGLang KV 传输限制），复用 DP 通信域；不向其他 CP 实现推广。
- 带序列依赖的卷积需要处理跨分片状态，不能直接沿用 Attention 的切分；GDN 的固定实现与后续受门控路径按模型 Guide 分别核对。
- KV 汇聚开销需明确总序列还是每 rank 长度固定、统计单 rank 还是全域后计算；这里不作随 CP size 线性增长的通用承诺。
- 本卡固定证据集中于长序列 Prefill；不能由单 token 描述推出所有 CP 实现都不支持 Decode。
- TP 口径：部署图 CP4×局部 TP2 对应启动参数整体 tp_size=8；cp_size=4、8%4=0 满足接口约束。图中的局部 TP2 不能直接与启动参数 tp_size 比较，两者不是互斥方案。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md)（primary）
- [qwen3_next_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md)（supporting）
- [0001-support-gdn-cp.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch)（implementation）
- [sgl_kernel_npu_support_gdn_cp.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/sgl_kernel_npu_support_gdn_cp.patch)（implementation）

## Known Deployments

- **Qwen3-Next Prefill**（[qwen3-next](../models/qwen3_next.md)）：默认仅 Gated Attention 层启用 CP+TP，GDN 层保持纯 TP（Conv1d 默认不切 Sequence）。以 CP4·TP2、64K 输入为例，每 rank 处理 16K Q token，KV 通过 AllGather 汇聚；Attention 结束后 Reduce-Scatter 进 MoE。GDN 经 `ENABLE_CONTEXT_PARALLEL_GDN=1`（默认 false）可走 env-gated GDN-CP（overlap 窗口 P2P + conv_state 末 rank 广播绕开序列依赖），详见 [qwen3-next](../models/qwen3_next.md)；ZigZag 负载均衡仍仅作用于 Gated Attention 层。
- 上述 Qwen3-Next 接口与本仓[Qwen CP/TP 案例](../../optimizations/cases/qwen3_next_a3_prefill_cp_tp.md)一致；[DeepSeek/Kimi 整域 CP 案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)是另一实现，不能拼接限制。

## Links

- [tensor-parallel](tensor_parallel.md)
- [data-parallel](data_parallel.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [zigzag-cp](zigzag_cp.md)
- [gated-attention](../modules/gated_attention.md)
- [inference-config](../techniques/inference_config.md)
- [deepseek-v4](../models/deepseek_v4.md)（Prefill 长序列 Attention 选 CP + zigzag 切分）
- [glm-5](../models/glm_5.md)（GLM-5 Prefill 长序列 CP，cp_size=world_size）
- [custom-cp-dsa](../../../training/concepts/parallelism/custom_cp_dsa.md)（跨域·训练：DSA 专用自定义 CP（KV 序列维 AllGather））
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 5D 并行枢纽，CP8 维在 5D 装配中的位置与基础 CP 机制对照）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)（Cosmos 世界模型多卡 CP 序列并行）
- [context-parallel-train](../../../training/concepts/parallelism/context_parallel_train.md)（跨域·训练：MindSpeed CP 家族 Ulysses / Ring / Hybrid / Unaligned，含前反向两段通信与 KV 缓存）
