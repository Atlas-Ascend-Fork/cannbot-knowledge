---
type: Concept
title: SGLang
description: 开源 LLM 推理服务框架，在 cann-recipes-infer 中作为多个模型的基础推理引擎，提供原生的并行能力（TP、EP、DP）和在线推理服务能力。
tags:
- task.implementation
- topic.architecture
- topic.mixture_of_experts
- topic.kv_cache
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3-next/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3-moe-sglang/README.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# SGLang

## Summary

开源 LLM 推理服务框架，在 cann-recipes-infer 中作为多个模型的基础推理引擎，提供原生的并行能力（TP、EP、DP）和在线推理服务能力。

## Architecture

- 支持 Online/Offline 推理模式
- 内置调度器、KVCache 管理、并行策略
- cann-recipes-infer 在其基础上集成了 NPU 专用的优化和算子

## Key Features

- 原生 Tensor Parallel / Expert Parallel / Data Parallel 支持
- 动态 Batch 调度
- KVCache 管理与 Paged Attention
- Prefill-Decode 分离部署（PD 分离）——cann-recipes-infer 自研 executor 的在线 PD 分离实现（[online-pd-inference](online_pd_inference.md)）在 `MetadataBufferPool` 直写、`retract_decode` 驱逐等设计上对齐 sglang

## Usage Scenarios

- LLM 在线推理服务部署
- 多模型多并行策略的统一推理框架

## Constraints

- NPU 适配需要额外的 patch 和算子替换
- 部分高级特性（如 CP）需在框架外实现

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — 多个模型基于 SGLang 框架部署

## Known Integrations

- **Qwen3-Next** 基于 SGLang v0.5.6 + 六个 stage patch（stage1 适配与 MoE 多流，stage2 W8A8/C8 量化，stage3 GDN+MTP，stage4 CP+ZigZag，stage5 GDN/rmsnormgated 融合算子接入，stage6 GDN 的 CP+TP 混合并行 / `ENABLE_CONTEXT_PARALLEL_GDN`，对应 `patches/stage6/0001-support-gdn-cp.patch`）完成 NPU 部署。
 - 新增入口：`zigzag_cp_utils.py`、`get_cp_group` / `context_model_parallel_all_gather`、`fused_gdn_gating.py`、`ascend_backend.py` C8 路径、`eagle_worker_v2.py` MTP v2。
 - 使能方式由 `set_env.sh` 环境变量控制（`ENABLE_ASCENDC_FUSION_GDN`、`USE_CUSTOM_NORM_KERNEL`、`ENABLE_NPU_DEEPEP_MOE_MULTI_STREAM`、`ASCEND_USE_C8`、`CP_USE_ZIGZAG`、`SGLANG_ENABLE_SPEC_V2` 等）。

## Links

- [atlas-a3](../platforms/atlas_a3.md)
- [qwen3-next](../models/qwen3_next.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [online-pd-inference](online_pd_inference.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [vllm-ascend](../../../training/concepts/frameworks/vllm_ascend.md)（跨域·训练：同类 LLM 推理服务框架(RL rollout 后端)）
