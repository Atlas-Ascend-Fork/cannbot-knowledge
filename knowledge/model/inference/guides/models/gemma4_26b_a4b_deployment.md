---
type: Guide
title: Gemma-4 文本 Decoder 的 A2/A3 部署与精度验收
description: Gemma-4 文本 Decoder 的 A2/A3 部署与精度验收，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/models/modeling_gemma4.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/config/gemma4_rank_8_8ep_gegraph_decode.yaml
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-21T09:56:17Z'
platforms:
- a2
- a3
---

# Gemma-4 文本 Decoder 的 A2/A3 部署与精度验收

## 目标、输入与产物

面向固定来源中的 Gemma-4-26B-A4B 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/gemma4_26b_a4b.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 限定文本路径并保存环境

本流程仅 Language MoE Decoder，Vision Tower、W8A8/W4A16 与 sliding 环形缓存不在已覆盖路径中。README/requirements 的 transformers 5.0.0 与建模头部 5.5.0 标注不同，保存实际版本，不自动选择一方。

## 2. 核对 EP8 与异构 cache

固定样例为 `attn_tp=1`、`dense_tp=1`、EP8、Embedding/LMHead TP8。Sliding/full 层缓存分别按本层 KV 维度分配连续缓冲，不直接套用统一 Paged block；full 层 K=V 与 `scale=1.0` 必须对齐模型配置。全局机制见 [KV 管理](../../concepts/frameworks/kv_cache_manager.md)、[EP](../../concepts/parallelism/expert_parallel.md)。

## 3. 分别验收 Decode 路由和图后端

`custom_params.moe_ep_decode_mode` 的 mc2 与 local_experts 为替代路径：前者 dispatch_v2/combine_v2，后者本地专家掩码计算后 AllReduce，保持静态 shape。代码默认按 experts_per_rank≤24 选择 mc2，EP8 为16/rank；实际 YAML 显式 local_experts，最终以生效配置为准。A2 算子上限不能推广为 A3 的限制。

GE Decode 用 torchair 接口与 Tensor 实际长度，npugraph_ex 路径按其接口所需 host list 处理；Prefill 保持 eager。RoPE cos/sin 预计算避免图内 `.item()`，相关决策见 [图模式规则](../../optimizations/rules/graph_mode_enable_decision_profiling.md)。不同后端的长度类型不得互换。

## 4. 检查数值替代与能力缺口

Full partial RoPE 使用 slice→rotary_mul→cat。Decode 手工 GEGLU 的 `npu_fast_gelu(gate)*up` 与报告中的 F.gelu 表述不同；当前代码注释说明后者有 capture 回退问题。Prefill/eager 的 npu_geglu 与 Decode 路径可能不 bit-exact，不能依据“语义连贯”验收精度。npu_ffn 的 FP16、npu_gelu_mul 的维度限制只按对应固定来源解释，不当作未来版本全局约束。

性能分开查阅 [A2 观测](../../optimizations/benchmark_observations/gemma4_a2_source_benchmark.md)、[A3 观测](../../optimizations/benchmark_observations/gemma4_a3_source_benchmark.md)；A2 累计表与跨硬件表口径不同，不拼接成一次试验。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/models/modeling_gemma4.py)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/config/gemma4_rank_8_8ep_gegraph_decode.yaml)
