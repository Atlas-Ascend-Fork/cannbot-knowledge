---
type: Concept
title: Context Parallel
description: 将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# Context Parallel

## Summary

将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。

## Mechanism

- 将 Sequence 切分为多个 chunk，每个 Rank 处理一个 chunk
- Attention 计算前通过 AllGather 收集完整的 KV
- 每个 Rank 用自己的 Q chunk 和完整 KV 计算 Attention
- 计算后通过 ReduceScatter 聚合结果
- 通常复用 DP 通信域

## Applicable Scenarios

- Prefill 阶段的长序列处理（64K+ tokens）
- Attention 计算量 O(S²) 使得长序列下单卡 OOM 风险高
- 适用于标准 Attention 和 GatedAttention 等结构

## Configuration

- `cp_size < tp_size`（CP 仅 PD 分离场景可开，复用 DP 通信域故与 DP 互斥）
- 典型配置如 mCP * nTP（如 CP4 * TP2）
- 需配合 ZigZag 负载均衡解决因果注意力的计算不均

## Constraints

- `cp_size < tp_size`（PD 分离 kv 传输逻辑限制，cp_size 上限由 tp_size 决定）；CP 仅 PD 分离场景可开，复用 DP 通信域故与 DP 互斥
- 沿 Sequence 的卷积操作不适合 CP 切分（如 GDN 模块）
- AllGather 通信量随 CP size 线性增长
- 仅适用于 Prefill 阶段（Decode 阶段单 token 无需 CP）
- 口径差异：Known Deployments 的 64K·CP4·TP2 取自 opt doc 部署示例的 m=4(CP)·n=2(TP) 口径（cp=4>tp=2）；README 接口约束写 `cp_size < tp_size`——两处口径不同，引接口约束为准。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — Qwen3-Next 等模型在 Prefill 阶段使用 CP+TP 混合并行

## Known Deployments

- **Qwen3-Next Prefill**（[qwen3-next](../models/qwen3_next.md)）：默认仅 Gated Attention 层启用 CP+TP，GDN 层保持纯 TP（Conv1d 默认不切 Sequence）。以 CP4·TP2、64K 输入为例，每 rank 处理 16K Q token，KV 通过 AllGather 汇聚；Attention 结束后 Reduce-Scatter 进 MoE。GDN 经 `ENABLE_CONTEXT_PARALLEL_GDN=1`（默认 false）可走 env-gated GDN-CP（overlap 窗口 P2P + conv_state 末 rank 广播绕开序列依赖），详见 [qwen3-next](../models/qwen3_next.md)；ZigZag 负载均衡仍仅作用于 Gated Attention 层。
- CP 复用 DP 通信域，因此与 DP 互斥；通过 `--cp-size` 使能；`CP_USE_ZIGZAG=1` 开启 [zigzag-cp](zigzag_cp.md)；仅在 PD 分离场景支持。

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

<!-- cannbot:related:start -->
## 相关

- [CP/DCP 在线-softmax 跨卡合并只 mask lse 不 mask out 污染归并——本卡对某序列无 KV 时须对 attn_out 施同一 batch_seq_mask 置 0](../../runbooks/precision/cp_dcp_online_softmax_merge_mask_out_not_only_lse.md)（`related`）：在线-softmax 跨卡合并把每卡的 (out, lse) 两路一起喂给归并算子。；将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。。运行手册处理的每卡 out/lse 合并正发生在 Context Parallel 按序列分片之后，是 CP attention 结果恢复的精度环节。
- [KVP — 长序列 memory-bound decode 沿 S 维切 KV Cache（lse-softmax 在线归约 + 耦合配置约束）](../../guides/experience/interventions/kvp_longseq_decode.md)（`related`）：KVP 配置矩阵明确“｜ `cp_size == 1` ｜ KVP 与 ［context-parallel］(../../../concepts/parallelism/context_parallel.md) 都沿 S 维切、互斥 ｜”；CP 卡定义“将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。”，两卡共同提供沿序列维并行时的互斥选型边界。
- [Prefill 上下文并行下多模态推理静默掉精度：非连续/非单调 position 与 embedding 错位](../../runbooks/precision/pcp_multimodal_noncontiguous_position.md)（`related`）：Prefill 阶段开启上下文并行（沿 Sequence 维切分请求 token 到多个 worker，`cp_size > 1`）。；将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。。运行手册的故障触发点正是概念页定义的 Sequence 维 Context Parallel 切分，并进一步限定到多模态 position 与 embedding 对齐。
- [SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径](../../guides/experience/interventions/sfa_dsa_cp_cross_group_kv_allgather.md)（`related`）：本页给出该场景下的一个可执行做法：**在注意力/indexer 计算前，先 `index_select` 出有效 block、再依次做 DCP all_gather 和 PCP all_gather 重建完整 KV**，并配套一条**硬前置**——`kv_cache_interleave_size` 必须等于 `block_size`。；将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。指南把 Context Parallel 的 Sequence 分片机制具体化为 DSA/SFA 的 DCP 后 PCP KV 重建顺序和块对齐合同。
- [ZECO — 让线性注意力 / GDN 吃到序列并行（Context Parallel），打破 chunk 递推的跨 rank 顺序依赖](../../guides/experience/interventions/qwen3_next_gdn_context_parallel_zeco.md)（`related`）：ZECO 卡把递推改写为“**一次轻量的跨 rank 状态传播**得到每个 rank 的 initial_state，再用 `h_t = a·h_0 + b` 本地还原状态、出输出——不再需要按 rank 顺序滚算 `h`。”；CP 概念卡定义“将 Sequence 切分为多个 chunk，每个 Rank 处理一个 chunk”，前者正是让 GDN 满足后者序列分片执行形态的专用状态传播机制。
- [ZigZag Context Parallel (Load-Balanced Causal Attention)](zigzag_cp.md)（`related`）：ZigZag 是 ［context-parallel］(context_parallel.md) 下针对**因果 Attention 负载不均**的切分变体：将输入 Sequence 切成 `2·cp_size` 个 block，每个 CP rank 负责头尾对称的两个 block（如 rank 0 负责 block 0 与 block 2·cp_size-1），从而让所有 rank 的历史 KV 计算量近似相等。；需配合 ZigZag 负载均衡解决因果注意力的计算不均。ZigZag 卡给出头尾对称分块以均衡历史 KV 计算量的具体策略，Context Parallel 卡明确把 ZigZag 作为因果注意力负载不均的配套方案，形成基础并行到负载均衡变体的直接链。
- [长序列 Prefill 注意力优先 Context Parallel（CP 仅 prefill 生效，MoE 复用 CP 域走 EP）](../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)（`related`）：“长序列 Prefill（本经验覆盖 16K–166K，示例常以 64K 计），注意力单 rank 要承担整条序列的计算量与 activation 内存，OOM 风险高、TTFT 难控。此时注意力**优先选 ［context-parallel］(../../../concepts/parallelism/context_parallel.md)（CP）**，把序列维切到多 rank 均摊，单 rank 计算量与 activation 内存都变小、TTFT 可控。”；“- Attention 计算前通过 AllGather 收集完整的 KV”。概念卡给出规则所采用的 Sequence 切分、完整 KV 收集和本地 Q 计算合同。
- [MindSpeed 上下文并行家族（Ulysses / Ring / Hybrid / Unaligned CP）](../../../training/concepts/parallelism/context_parallel_train.md)（`same_topic`）：将输入序列沿 Sequence 维度切分到多个 Rank 并行处理的策略，用于解决长序列场景下单卡激活值内存不足的问题。通常与 TP 组合使用。；MindSpeed 训练侧用 **Context Parallel（CP，长序列并行）** 沿 Sequence 维把输入切到 `context_parallel_size` 个 rank，把 Attention 的 `O(S²)` 激活/计算压到单卡可承受。。两卡围绕同一 CP 核心对象，前者给出推理抽象，后者给出训练侧切分语义。
<!-- cannbot:related:end -->
