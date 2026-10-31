---
type: Concept
title: Tensor Parallel
description: 将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。具体使用模块与阶段由模型实现决定，也可与 DP/EP 配合。
tags:
- task.design
- topic.parallelism
- topic.model_architecture
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen/qwen_dense_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- a3
---
# Tensor Parallel

## Summary

将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。Attention、FFN 是否使用 TP 以及在哪个阶段使用，由具体模型实现与部署配置决定，也可采用 DP/EP。

## Mechanism

- 权重沿特定维度切分到多个 Rank
- 每个 Rank 独立计算各自的分片
- 通过 AllReduce 或 ReduceScatter 通信聚合结果
- 典型切分维度：Attention Head 维度、FFN 隐藏维度

### 通算融合（Matmul + AllReduce）

行并行层（如 `down_proj`、`o_proj`）在分片 Matmul 后需要一次 AllReduce 聚合，通信可能暴露在关键路径上。`torch_npu.npu_mm_all_reduce_base(reduce_op="sum")` 可将该 Matmul 与其后 AllReduce **融合为一个算子**，减少通信暴露。[qwen3-5-moe](../models/qwen3_5_moe.md) 的 Prefill 路径以此为实例（`qwen3_5_prefill_mm_all_reduce`，开关 `custom_params.enable_mm_all_reduce_base` 默认 False，仅 Prefill、TP 切分数 >1、输入已按 TP 切分、线性层无bias且满足当前量化/平台门控、能取到 HCCL group name 时启用，否则走对应模型普通Matmul/量化及规约路径；当前Qwen3.5还支持950的部分低精度融合分支，A3量化与MXFP8+GE被拒绝）。

## Applicable Scenarios

- 支持对应分片算子和通信路径的 Attention/FFN 层
- 参数超出单卡容量时可与其他切分策略比较，不由容量问题单独决定必须采用 TP
- Decode 阶段的基础并行策略

## Configuration

- 按 head 切分的 Attention TP 受该实现的 head 布局限制；o_proj、MLP、embedding 等独立 TP 组还需按各自接口判断。
- 典型取值：TP2、TP4、TP8

## Constraints

- TP 通信（AllReduce）开销随 TP size 增大而增加
- 纯权重TP不自动解决所有序列内存问题；可结合SP/CP，但须按模型缓存与通信实现核对
- Head 数量不能作为所有模块 TP 组的通用上限；模型特定上限按对应 Guide 和固定实现核对。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/README.md)（primary）
- [qwen_dense_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen/qwen_dense_optimization.md)（supporting）
- [qwen3_next_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md)（supporting）

## Known Deployments

- **Qwen3-Next**（[qwen3-next](../models/qwen3_next.md)）：Attention Head=16 决定纯 TP 上限 16。Prefill 下 Gated Attention 走 CP+TP（[context-parallel](context_parallel.md)），GDN 默认走纯 TP（经 `ENABLE_CONTEXT_PARALLEL_GDN=1`（默认 false）可改走 env-gated GDN CP+TP 混合，详见 [qwen3-next](../models/qwen3_next.md)）；Decode 下 Attention/GDN 走 TP，MoE 走 EP。GDN 的 TP 上限由 num_kv_head 决定，README 约束 `tp_size ≤ 32`。
- **Qwen Dense**（[qwen-dense](../models/qwen_dense.md)）：Qwen2/Qwen3 稠密模型的纯 TP 路径。Attention QKV 按头切 + `o_proj` 行切（`merged_qkv_proj` 合并 Matmul），MLP `gate_up_proj` 列切 + `down_proj` 行切；`models/qwen/config/` 提供 1tp（单卡）/ 2tp（`attn_tp_size=2`、`embed_tp_size=1`、`lmhead_tp_size=2`）模板。
- **DeepSeek-R1**（[deepseek-r1](../models/deepseek_r1.md)）：Prefill 长序列/短请求场景走 [sp-tp-sp](sp_tp_sp.md)（SP 切 token → FA 内 TP 切 head → SP）；纯 TP 路径仅在 `decode_r1_rank_16_16tp_a8w8.yaml` 这种 `moe_tp_size > 1` 的特殊配置下启用，走 `moe_infer_tp` 分支。主流 R1 部署 `attn_tp_size=dense_tp_size=moe_tp_size=1`，MLA 与 MoE 都以 DP/EP 方式部署。`embed_tp_size` / `lmhead_tp_size` 单独控制 embedding / lm_head 的 TP 切分。
- **Hy3**：当前A3和950配置有独立denseTP/SP组合，已迁models/hy3并启用MTP1；不再用旧Hy3-preview全模块TP4样例代表默认值。见[当前部署](../../guides/models/hy3_preview_deployment.md)。
- **LongCat-Flash-Lite**：当前保留全TP和EP配置，N-gram词表独立分片；Prefill可用SP，不能从旧Decode attnTP数推导Prefill无序列切分。见[当前部署](../../guides/models/longcat_flash_lite_deployment.md)。

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
- [hy3-preview](../models/hy3_preview.md)（各平台当前并行配置由Guide维护）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（8tp 全模块 TP=8，N-gram 子表 TP 切分）
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 5D 并行枢纽，TP4 非 MoE+共享专家张量并行、q_lora Matmul sharding 优化）
- [tensor-parallel-2d](../../../training/concepts/parallelism/tensor_parallel_2d.md)（跨域·训练：MindSpeed 高维张量并行，把本页单 `tp` 通信域分解为 `tp_x×tp_y` 正交子域以降低大 TP 域通信量）
