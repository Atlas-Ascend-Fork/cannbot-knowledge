---
type: Concept
title: Atlas A3
description: Atlas A3 是昇腾训练与推理产品系列之一。本页汇总知识库中明确声明适用于 A3 的模型实践；是否支持 A3 仍以各模型卡及其固定来源为准，不能由仓库归属统一推断。
tags:
- task.lookup
- topic.architecture
status: stable
sources:
- resource: https://gitcode.com/cann/hccl/blob/cda1ba007461dc54732744b5228e63a0847a79b6/examples/04_custom_ops_p2p/README.md
  role: primary
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-21T10:09:34Z'
platforms:
- a3
---
# Atlas A3

## Summary

Atlas A3 是昇腾训练与推理产品系列之一。固定版本 HCCL 样例明确把 Atlas A3 训练系列产品和推理系列产品列入支持范围。本页只汇总知识库中已经由各自来源声明 A3 适用性的模型实践；它不表示所有 `cann-recipes-infer` 模型都支持 A3，也不替代具体产品规格文档。

## 范围边界

- 本页不声明峰值算力、内存容量、节点卡数或互联拓扑；这些参数应引用对应产品规格。
- 模型是否支持 A3，以该模型卡的 `platforms` 和固定来源为准。
- 与 A2、Ascend 950 或 950 的差异，只保留在具有直接证据的专题卡中。

## Evidence

- [HCCL 自定义 P2P 样例](https://gitcode.com/cann/hccl/blob/cda1ba007461dc54732744b5228e63a0847a79b6/examples/04_custom_ops_p2p/README.md) — 固定版本环境要求列出 Atlas A3 训练系列产品与 Atlas A3 推理系列产品。

## Known Deployments

- **Qwen Dense**（[qwen-dense](../models/qwen_dense.md)）：Qwen2/Qwen3 稠密模型（Qwen3-8B、Qwen2.5-7B-Instruct）BF16 单卡 / 2 卡 TP 部署（源 README 同列 Atlas A2，A2 无独立平台页）。
- **Qwen3-Next-80B-A3B-Instruct**（[qwen3-next](../models/qwen3_next.md)）
 - BF16 PD 混部：TP16 + DP8 + EP + DeepEP，`context-length 262144`、`chunked-prefill-size 71680`。
 - A8W8C8 大 EP：dp_size=8、tp_size=2、ep_size=16，256K 输入下纯模型 decode 时延 **20.6 ms**（graph_bs=16，16die）。
 - PD 分离 + CP：Prefill `--cp-size 8`、ZigZag 负载均衡（[zigzag-cp](../parallelism/zigzag_cp.md)）。
- **DeepSeek-R1**：平台部署见[模型Guide](../../guides/models/deepseek_r1_deployment.md)，性能与单位分歧见[R1 Prefill 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)、[R1 Decode 来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_decode_source_benchmark.md)；本平台入口不从world_size裁决物理卡数。
- **Gemma-4-26B-A4B**：模型结构见[Concept](../models/gemma4_26b_a4b.md)，配置见[Guide](../../guides/models/gemma4_26b_a4b_deployment.md)，A3数据见[Gemma A3来源观测](../../optimizations/benchmark_observations/gemma4_a3_source_benchmark.md)。
- **Hy3-preview**：结构见[Concept](../models/hy3_preview.md)，配置见[Guide](../../guides/models/hy3_preview_deployment.md)，分阶段数据见[Hy3来源观测](../../optimizations/benchmark_observations/hy3_a3_source_benchmark.md)。

## Links

- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [qwen-dense](../models/qwen_dense.md)
- [deepseek-r1](../models/deepseek_r1.md)
- [deepseek-v4](../models/deepseek_v4.md)（A3 Pod 64 卡 W8A8C16 部署；V4 另支持 Ascend 950PR/DT 代际）
- [gemma4-26b-a4b](../models/gemma4_26b_a4b.md)（结构、配置和观测分别维护）
- [hy3-preview](../models/hy3_preview.md)（结构、配置和观测分别维护）
- [ascend-950](ascend_950.md)（代际对照：A3 = CV1:2 / sort32-mrgsort LI Top-k / 无原生 FP8 / weightNZ 启用 vs 950 = Histograms / 原生 FP8-MXFP4 / weightNZ 关闭）
- [int8-int4-hybrid](../quantization/int8_int4_hybrid.md)（A3 Pod 上 V4 的 Int8 W8A8C16 + Hybrid INT8-INT4 量化方案）
- [sglang](../frameworks/sglang.md)
- [torchair](../frameworks/torchair.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)
- [torchtitan-5d-parallel](../../../training/concepts/parallelism/torchtitan_5d_parallel.md)（跨域·训练：DeepSeek-V3.2 671B 在 64 卡 A3 的最小化切分，5D 并行枢纽）
- [deepseek-v4-continue-pretrain](../../../training/guides/recipes/deepseek_v4_continue_pretrain.md)（跨域·训练：A3 64/192 卡 V4 续训）
- [autofuse-train](../../../training/concepts/techniques/autofuse_train.md)（跨域·训练：A3 上 AutoFuse 训练入图）
- [deepseek-r1-rl](../../../training/guides/recipes/deepseek_r1_rl.md)（跨域·训练：A3 SuperPoD 128 卡 DeepSeek-R1 GRPO RL，HCCS 高带宽支撑训推切换与多流掩盖）
- [vllm-ascend](../../../training/concepts/frameworks/vllm_ascend.md)（跨域·训练：A3 上 veRL RL 的 vLLM-Ascend rollout 后端）
- [qwen3-rl](../../../training/guides/recipes/qwen3_rl.md)（跨域·训练：Qwen3 235B/32B RL on A3）
- [atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)（跨域·空间智能：空间智能样例目标平台 Atlas A2，同属昇腾 Atlas 系列）
- 跨域·具身：[cosmos-transfer2.5](../../../embodied/concepts/world_models/cosmos_transfer2_5.md)、[cosmos-predict2.5](../../../embodied/concepts/world_models/cosmos_predict2_5.md)、[isaac-gr00t](../../../embodied/concepts/manipulation/isaac_gr00t.md)、[ascend-310p](../../../embodied/concepts/platforms/ascend_310p.md)、[ddp-static-graph](../../../embodied/concepts/techniques/ddp_static_graph.md)、[gradient-checkpoint-refine](../../../embodied/concepts/techniques/gradient_checkpoint_refine.md)（具身样例在 Atlas A3 的训练 / 推理）
