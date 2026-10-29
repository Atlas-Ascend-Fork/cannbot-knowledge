---
type: Concept
title: NPU 图模式（ge_graph / npugraph_ex）
description: 解释 GE 编译与 npugraph_ex 捕获重放两条执行路径；阶段路由和配置限固定版本，选型、实施、排障及未核实观测分别链接对应入口。
tags:
- task.optimization
- topic.model_architecture
- topic.attention
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/cann/npu_graph_optimization.md
  role: supporting
created_at: '2026-04-15T00:00:00Z'
updated_at: '2026-10-21T01:51:39Z'
platforms:
- agnostic
---

# NPU 图模式（ge_graph / npugraph_ex）

## Summary

Pytorch 默认 `eager` 模式"边解释边执行"，逐算子下发 Device，推理场景容易暴露 Host 侧下发开销（**host bound**）。图模式通过 `torch.compile` 把前向逻辑捕获成图、交给 NPU 后端编译执行，**减少 Host 下发开销，允许后端在更大范围做融合、内存复用、调度优化**，显著降低 decode 时延。

NPU 图模式有两种实现路径：**GE 图模式**（FX → Ascend IR → GE 引擎编译）与 **npugraph_ex**（基于 npugraph capture & replay，强调下沉调度与低开销执行）。历史代码里的 `acl_graph` 命名对应当前 `npugraph_ex`，**将逐步废弃**。

cann-recipes-infer 通过 [cann-executor](../frameworks/cann_executor.md) 的 `model_config.exe_mode` 配置开关，图模式开关**仅对 decode 生效**，该版本 prefill 走 eager；这不构成所有 Prefill 或动态 shape 不宜入图的结论。

## Mechanism

### GE 图模式 vs npugraph_ex 对比

| 维度 | `ge_graph` | `npugraph_ex` |
|------|-----------|---------------|
| 实现路径 | FX → Ascend IR → GE 引擎编译执行 | npugraph capture & replay，下沉调度 |
| 配置承载 | `CompilerConfig.experimental_config` 成员 | `options` kwargs |
| 普通编译后端 | `backend = tng.get_npu_backend(...)` | `backend = "npugraph_ex"` |
| 缓存编译接口 | `tng.inference.cache_compile(...)` | `torch.npu.npugraph_ex.inference.cache_compile(...)` |
| `dynamic` 默认 | `False` | `True` |
| 专属配置项 | `frozen_parameter` / `tiling_schedule_optimize` / `topology_sorting_strategy` | `static_kernel_compile` / `frozen_parameter` |
| 特性支持 | 支持 [superkernel](superkernel.md) | 支持 `enable_static_kernel` |
| 推荐场景 | 功能稳定、性能更优，当前默认首选 | 使用体验接近 eager，后续主推；算子接口补齐 Tensor 输入后会调整 `dynamic` |

> **为何 `npugraph_ex` 当前保持 `dynamic=True`**：并非图本身必须动态，而是**配套的 FIA 算子接口**里 `actual_seq_lengths` 等入参暂不支持 Tensor 输入，只支持 `list[int]`。若强行 `dynamic=False`，容易触发重编译。后续算子接口补齐 Tensor 输入支持，这里配置也会调整。

## 从图捕获到执行

`torch.compile` 捕获前向并交给所选后端；执行器决定在哪个阶段调用已编译函数。所引 Executor 版本只编译 Decode、Prefill 使用 eager，这是其执行策略，不是 Prefill 或动态 shape 不能入图的通用结论。编译缓存复用、guard、重捕获与运行时 replay 是不同层次的问题，诊断时分别确认。

## 决策、实施与排障入口

- [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)：按 Host 开销、正确性与净收益选择。
- [Decode 图编译指南](../../guides/optimization/graph_mode_decode_only_compile_backends.md)：来源执行器路由、适配、预热和验收。
- [编译缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)：持久缓存条件与边界。
- [重编译 Runbook](../../runbooks/performance/graph_mode_stable_input_signature_recompile.md)：从 guard 日志定位输入变化。
- [跨流同步 Runbook](../../runbooks/runtime/graph_mode_multi_stream_sync_failures.md)：事件、守卫和流对象失败签名。
- [待核验观测](../../optimizations/cases/graph_backend_layout_unverified_observations.md)：保存出处不足的布局兼容性、时延与配置记录，不用于通用选型。

## 固定来源的约束

- 仅 Decode 生效是所引 Executor 的路由约定，其他执行器应分别核对。
- **`ge_graph` + SuperKernel 可组合**（如 DeepSeek-R1 `decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml`）；所引版本未提供 npugraph_ex 的同一 SuperKernel 路径。
- **MTP 与图模式的兼容性按模型而异**：DeepSeek-R1 `ge_graph + MTP1` 可共存；Qwen3-Next 的 MTP 与 SGLang ACLGraph 互斥。见 [mtp-speculative-decoding](mtp_speculative_decoding.md)。
- 所引 Executor 的 `enable_static_kernel` 只在 npugraph_ex 路径启用。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/cann/npu_graph_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/cann/npu_graph_optimization.md)（全文 270 行，涵盖原理、两种模式对比、使能链路、五条件、FIA 建议、Troubleshooting）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/utils/graph_utils.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/utils/graph_utils.py)（`compile_model_forward`）、[`executor/core/model_worker/model_worker.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/model_worker/model_worker.py)（`compile_model`）、[`executor/core/engine/execution_engine.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/executor/core/engine/execution_engine.py)（`warm_up`）
- 官方资料：[TorchAir 文档总览](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh)、[GE / Ascend IR](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh/ascend_ir/ascend_ir.md)、[npugraph_ex 后端](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/docs/zh/npugraph_ex/npugraph_ex.md)

## Links

- [torchair](../frameworks/torchair.md)
- [cann-executor](../frameworks/cann_executor.md)
- [inference-config](inference_config.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [qwen-dense](../models/qwen_dense.md)（覆写 `ModelRunner.graph_compile`；`ge_graph` + `npugraph_ex` 均已验证）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（Decode 整图、Prefill eager；`ge_graph` 默认 / `npugraph_ex` 备选，A3 上 ge_graph 稳态更优、npugraph_ex 编译更快）
- [hy3-preview](../models/hy3_preview.md)（`ge_graph` Decode 整图、Prefill eager；MC2 dispatch/combine 替代手动 all_to_all 消除 graph break）
- [superkernel](superkernel.md)
- [mtp-speculative-decoding](mtp_speculative_decoding.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [aicpu-scheduler](aicpu_scheduler.md)（值依赖分核下沉 AICPU，aclgraph 友好、metadata 单次复用）
- [autofuse](../frameworks/autofuse.md)（`torch.compile` 下游的 Inductor NPU 自动融合 Codegen 后端；图捕获/执行在前，AutoFuse 做 vector 子图融合编译）
- [longcat-flash-lite](../models/longcat_flash_lite.md)（LongCat-Flash 减配验证模型，`ge_graph` 后端 Decode 整图（`fullgraph=True`）、Prefill eager；NgramEmbedding 整体入图、MoE identity expert 用乘法掩码绕过 GE 不支持布尔索引）
- [sam-speculative](../../../training/concepts/techniques/sam_speculative.md)（跨域·训练：Qwen3 RL 中 npugraph_ex 与 SAM 叠加 +29~33%）
- [qwen3-rl](../../../training/guides/recipes/qwen3_rl.md)（跨域·训练：Qwen3 RL 使能 npugraph_ex 图模式）
- [hunyuan3d](../../../spatial/concepts/models/hunyuan3d.md)（跨域·空间智能：Hunyuan3D shapegen 图模式适配）
- [multi-stream](multi_stream.md)（多流编排在 ge_graph / npugraph_ex 图模式下落地，切流/同步/控核接口随执行路径不同）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[pi0](../../../embodied/concepts/manipulation/pi0.md)、[isaac-gr00t](../../../embodied/concepts/manipulation/isaac_gr00t.md)、[pi05](../../../embodied/concepts/manipulation/pi05.md)、[om-atc-offline](../../../embodied/concepts/techniques/om_atc_offline.md)、[flow-matching-action-expert](../../../embodied/concepts/modules/flow_matching_action_expert.md)（VLA 在线推理 / OM 离线用图模式）

## Notes

- **ambiguity**：旧代码/文档里 `acl_graph` 命名仍存在，但**当前应对应 `npugraph_ex`**；新接入模型按 `ge_graph` / `npugraph_ex` 配置。