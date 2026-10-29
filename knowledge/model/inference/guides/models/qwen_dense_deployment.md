---
type: Guide
title: Qwen Dense A2 的变体、图模式与量化验收流程
description: Qwen Dense A2 的变体、图模式与量化验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen/qwen_dense_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/qwen/qwen_dense_optimization.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen/models/modeling_qwen.py
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-21T09:56:20Z'
platforms:
- a2
---

# Qwen Dense A2 的变体、图模式与量化验收流程

## 目标、输入与产物

面向固定来源中的 Qwen Dense (Qwen2 / Qwen3 非 MoE) 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/qwen_dense.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 确认变体与权重

Qwen3-8B启用 QK-Norm、attention_bias=False；Qwen2.5-7B没有 QK-Norm、bias=True。核对实际 HF config、model_name与注册入口，不把同族 Qwen3-32B 架构表的标量当作8B/7B。此卡沿原 A2实践范围，来源另声明A3支持不替代目标平台验收。

## 2. 配置新执行器与 TP

4份YAML为qwen3_8b和qwen25_7b_instruct的1/2TP。新InferenceConfig路径的实际model_path、输入截断、scheduler batch/输出数、块式KV预算一起保存。Dense MLP按attn_tp_size切分，moe_tp_size在模板中存在并不表示模型含MoE。细节由 [TP机制](../../concepts/parallelism/tensor_parallel.md)、[KV管理](../../concepts/frameworks/kv_cache_manager.md)维护。

## 3. 验收融合与图后端

merged_qkv_proj、gate_up_proj加载后分别拆出Attention/MLP分支；非量化MLP为手写激活乘up，不能按MoE专家GroupedMatmul替换。Residual在层间传递，npu_add_rms_norm的输出/残差要同时核对。RoPE预计算、FIA v2实际长度与图编译入口随新/旧执行器区分。源README已验证特性表不等于本次硬件验证；npugraph_ex的static_kernel与GE配置分开保存。

## 4. 区分两个固定版本的量化能力

2c45117优化文档只述BF16，46485bef文档另含Qwen3-8B W8A8：权重per-channel、激活per-token，覆盖4个Linear；mm_quant_mode=w8a8int8和compressed-tensors权重共同决定路径。MLP使用npu_dequant_swiglu_quant的int32+scale→int8+scale链路。不得从后一个版本的说明反推前一个版本源码已含相同开关。

相关精度排查见 [转换/配置精度规则](../../optimizations/rules/precision_quant_convert_model_config_pitfalls.md)；源无端到端时延表，不新造基准。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen/qwen_dense_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/46485bef9bb6bf061e4c356942bfea395e75865a/docs/models/qwen/qwen_dense_optimization.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen/README.md)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen/models/modeling_qwen.py)
