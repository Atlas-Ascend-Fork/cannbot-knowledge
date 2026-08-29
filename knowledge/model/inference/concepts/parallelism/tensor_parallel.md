---
type: Concept
title: Tensor Parallel
description: 将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。几乎所有模型的 Attention 和 FFN 层都使用 TP。
tags:
- task.design
- topic.parallelism
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen/qwen_dense_optimization.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-11T00:00:00Z'
platforms:
- a3
---

# Tensor Parallel

## Summary

将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。几乎所有模型的 Attention 和 FFN 层都使用 TP。

## Mechanism

- 权重沿特定维度切分到多个 Rank
- 每个 Rank 独立计算各自的分片
- 通过 AllReduce 或 ReduceScatter 通信聚合结果
- 典型切分维度：Attention Head 维度、FFN 隐藏维度

### 通算融合（Matmul + AllReduce）

行并行层（如 `down_proj`、`o_proj`）在分片 Matmul 后需要一次 AllReduce 聚合，通信可能暴露在关键路径上。`torch_npu.npu_mm_all_reduce_base(reduce_op="sum")` 可将该 Matmul 与其后 AllReduce **融合为一个算子**，减少通信暴露。[qwen3-5-moe](../models/qwen3_5_moe.md) 的 Prefill 路径以此为实例（`qwen3_5_prefill_mm_all_reduce`，开关 `custom_params.enable_mm_all_reduce_base` 默认 False，仅 Prefill、TP 切分数 >1、输入已按 TP 切分、线性层无 bias / 非量化、能取到 HCCL group name 时启用，否则回退普通 Matmul + `dist.all_reduce`）。

## Applicable Scenarios

- 所有 LLM 的 Attention/FFN 层
- 模型参数量超过单卡 HBM 容量时必须使用
- Decode 阶段的基础并行策略

## Configuration

- TP size 受 Attention Head 数量限制（如 Qwen3-Next 的 16 heads 限制最大 TP16）
- 典型取值：TP2、TP4、TP8

## Constraints

- TP 通信（AllReduce）开销随 TP size 增大而增加
- 不解决 Sequence 维度的内存瓶颈（长序列需配合 CP）
- Head 数量是 TP size 的上限

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 所有模型均使用 TP 策略

## Known Deployments

- **Qwen3-Next**（[qwen3-next](../models/qwen3_next.md)）：Attention Head=16 决定纯 TP 上限 16。Prefill 下 Gated Attention 走 CP+TP（[context-parallel](context_parallel.md)），GDN 默认走纯 TP（经 `ENABLE_CONTEXT_PARALLEL_GDN=1`（默认 false）可改走 env-gated GDN CP+TP 混合，详见 [qwen3-next](../models/qwen3_next.md)）；Decode 下 Attention/GDN 走 TP，MoE 走 EP。GDN 的 TP 上限由 num_kv_head 决定，README 约束 `tp_size ≤ 32`。
- **Qwen Dense**（[qwen-dense](../models/qwen_dense.md)）：Qwen2/Qwen3 稠密模型的纯 TP 路径。Attention QKV 按头切 + `o_proj` 行切（`merged_qkv_proj` 合并 Matmul），MLP `gate_up_proj` 列切 + `down_proj` 行切；`models/qwen/config/` 提供 1tp（单卡）/ 2tp（`attn_tp_size=2`、`embed_tp_size=1`、`lmhead_tp_size=2`）模板。
- **DeepSeek-R1**（[deepseek-r1](../models/deepseek_r1.md)）：Prefill 长序列/短请求场景走 [sp-tp-sp](sp_tp_sp.md)（SP 切 token → FA 内 TP 切 head → SP）；纯 TP 路径仅在 `decode_r1_rank_16_16tp_a8w8.yaml` 这种 `moe_tp_size > 1` 的特殊配置下启用，走 `moe_infer_tp` 分支。主流 R1 部署 `attn_tp_size=dense_tp_size=moe_tp_size=1`，MLA 与 MoE 都以 DP/EP 方式部署。`embed_tp_size` / `lmhead_tp_size` 单独控制 embedding / lm_head 的 TP 切分。
- **Hy3-preview**（[hy3-preview](../models/hy3_preview.md)）：`attn_tp_size=dense_tp_size=embed_tp_size=lmhead_tp_size=4`（attn_tp 受 N_kv=8 约束，每 rank 2 个 KV head），`moe_tp_size=1`（MoE 走 EP=16）。Attention TP 与 MoE EP 在同一 16 die 部署中分工。
- **LongCat-Flash-Lite**（[longcat-flash-lite](../models/longcat_flash_lite.md)）：8tp 配置全模块 TP=8（MLA / Dense / MoE / Embedding / LM Head），`world_size=8`、单 batch 低时延；N-gram 12 子表 ~31 B 由 TP 切分（显存约束）。另有 8ep 路走 attn_tp=4 + EP=8。

## Links

- [context-parallel](context_parallel.md)
- [expert-parallel](expert_parallel.md)
- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [qwen-dense](../models/qwen_dense.md)
- [deepseek-r1](../models/deepseek_r1.md)
- [sp-tp-sp](sp_tp_sp.md)
- [deepseek-v4](../models/deepseek_v4.md)（Decode LM_head TP + o_a_proj 可选 TP）
- [hy3-preview](../models/hy3_preview.md)（attn/dense/embed/lmhead TP=4，MoE 走 EP=16）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（8tp 全模块 TP=8，N-gram 子表 TP 切分）
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 5D 并行枢纽，TP4 非 MoE+共享专家张量并行、q_lora Matmul sharding 优化）
- [tensor-parallel-2d](../../../training/concepts/parallelism/tensor_parallel_2d.md)（跨域·训练：MindSpeed 高维张量并行，把本页单 `tp` 通信域分解为 `tp_x×tp_y` 正交子域以降低大 TP 域通信量）

<!-- cannbot:related:start -->
## 相关

- [Attention-DP + MoE-EP 部署：对访存 / 内存重的投影层（O_proj / LM_Head / Embedding / dense）单独局部 TP](../../optimizations/experience/rules/local_tp_memory_heavy_projections.md)（`related`）：对访存 / 内存重的投影层单独开局部 ［tensor-parallel］(../../../concepts/parallelism/tensor_parallel.md)，把权重沿相应维切到多 rank 摊薄单 rank 显存 / 访存：；- 权重沿特定维度切分到多个 Rank - 每个 Rank 独立计算各自的分片 - 通过 AllReduce 或 ReduceScatter 通信聚合结果 - 典型切分维度：Attention Head 维度、FFN 隐藏维度。优化规则把 TP 机制限定到 O_proj、Embedding、LM_Head 和 dense 等重投影层，概念卡解释其权重切分与结果聚合机制。
- [TorchTitan 5D 并行与 DTensor Sharding 优化（DeepSeek-V3.2）](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（`related`）：将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。几乎所有模型的 Attention 和 FFN 层都使用 TP。；**TP**（`apply_non_moe_tp`）— 非 MoE 部分（embedding/norm/output、Attention、dense FFN）的张量+序列并行；详见 ［tensor-parallel］(../../../inference/concepts/parallelism/tensor_parallel.md)。前者定义 TP 的权重切分与适用层，后者把相同 TP 机制落实到 TorchTitan 5D 装配中的非 MoE 模块，形成概念到具体并行配置的使用链。
- [高维张量并行 TP-2D（MindSpeed 2D Tensor Parallel）](../../../training/concepts/parallelism/tensor_parallel_2d.md)（`related`）：TP-2D 把一维张量并行的单个 TP 通信域 `tp` 分解成两个正交子域 `tp_x × tp_y`（`tp = tp_x × tp_y`，二者均 > 1），让激活值与权重**同时在 first-dim（序列/输出维）与 last-dim（隐藏/收缩维）切分**。每个 Linear 的前向因此退化为「在一个子域 AllGather 序列 → 本地 matmul → 在另一个子域 ReduceScatter」的两段小域通信（如 fc1 取 AG=`tp_x`/RS=`tp_y`，fc2 两子域对调），而不是在整个大小为 `tp` 的域上做 AllGather/AllReduce。大 TP 域（如 `tp=16`）下，单次集合通信的参与卡数从 `tp` 降到 `tp_x` 或 `tp_y`，通信量与延迟随之下降。配套的**分布式 normalization** 只在 `tp_y` 子域做小 AllReduce（LayerNorm 两次：求和、平方和；RMSNorm 一次：平方均值）即可在不 AllGather 隐藏维的前提下完成逐 token 归一化。核心实现 `ParallelLinear2D` / `Linear2DSplitAlongFirstDim` / `LayerNorm2D` / `RMSNorm2D` 位于 ［mindspeed］(../frameworks/mindspeed.md) 的 `mindspeed/core/tensor_parallel/tp_2d/`，由 `--tp-2d --tp-x --tp-y` 启用。；将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。几乎所有模型的 Attention 和 FFN 层都使用 TP。。TP-2D 明确从一维 TP 通信域拆出两个正交子域并改变 Linear 的通信序列，候选说明一维 TP 的权重切分基线；二者共同给出从基础方案到二维扩展时保留与改变的核心语义。
<!-- cannbot:related:end -->
