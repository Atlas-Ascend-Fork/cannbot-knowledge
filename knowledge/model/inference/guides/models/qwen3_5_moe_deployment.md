---
type: Guide
title: Qwen3.5-MoE A3 三规格部署与 GDN 验收流程
description: Qwen3.5-MoE A3 三规格部署与 GDN 验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3_5/qwen3_5_moe_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/models/modeling_qwen3_5_moe.py
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_35b_ep8.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_122b_tp8.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_397b_tp16.yaml
created_at: '2026-10-21T09:56:19Z'
updated_at: '2026-10-21T09:56:19Z'
platforms:
- a3
---

# Qwen3.5-MoE A3 三规格部署与 GDN 验收流程

## 目标、输入与产物

面向固定来源中的 Qwen3.5-MoE 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/qwen3_5_moe.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定文本模型、版本与配置

流程覆盖文本侧；多模态 vision 外层不据此认定已适配。README 的 CANN9.0.0、下载链接8.3.RC1.alpha002、ChunkGDR 文档建议9.1.0不一致，记录实际包/接口与精度结果，不擅选版本。

| 规格 | 激活 | world_size | 并行 | exe_mode | YAML |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Qwen3.5-35B-A3B | A3B | 8 | EP8（`attn_tp=8`、`moe_tp=1`、`moe_ep=8`） | eager | `qwen3_5_35b_ep8.yaml` |
| Qwen3.5-122B-A10B | A10B | 8 | TP8（`attn_tp=8`、`moe_tp=8`、`moe_ep=1`） | ge_graph | `qwen3_5_122b_tp8.yaml` |
| Qwen3.5-397B-A17B | A17B | 16 | TP16（`attn_tp=16`、`moe_tp=16`、`moe_ep=1`） | ge_graph | `qwen3_5_397b_tp16.yaml` |

> 三份 YAML 均 `batch_size` 受严格约束（注释 `Strict constraint: Batch=1`，35B/122B 配 4、397B 配 1，源未解释差异 —— gap）。图模式仅在 TP 规格（122B/397B）默认开启。

## 2. 确认并行与执行模式

六路 TP 独立配置，MoE EP由 world_size/moe_tp 派生，linear attention 的 key/value head 数必须满足 attn_tp 整除。普通 EP 的恢复阶段用 index_select和一次finalize，不照搬 R1 的全套 routing 步骤；纯 EP Decode 还受 enable_decode_moe_dispatch_combine_v2、moe_ep>1、moe_tp=1 联合约束。

来源只确认 TP 配置的 GE Decode，Prefill eager初始化 KV/GDN 状态；npugraph_ex“暂未验证”。同一枚举出现在代码条件中不等于已验收。缓存见 [缓存规则](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)。

## 3. 分开验收三类实现条件

- Full attention：部分维度 MRoPE、FIA v2 TND、block cache 与实际长度共同验收，图/eager 的算子命名空间分开。
- GDN：Prefill torch_npu.npu_chunk_gated_delta_rule 与 PyTorch fallback 是替代路径；enable_gdn_solve_triangular 只影响后者。不要把 Qwen3-Next 的 PyPTO 实现或开关复制到此模型。in_proj_fused 同时产生 Q/K/V、Z、B/A，加载切分和dtype需一致。
- TP 通算融合：enable_mm_all_reduce_base 只在 Prefill、TP>1、输入已切分、无bias/非量化且有 HCCL group name 等条件成立时替代普通 Matmul+AllReduce。

## 4. 评测与未完成项

固定来源给 MMLU 脚本，未给端到端时延表或量化方案；thinking 配置与 HCCL AIV 的精度影响分开记录。35B/122B batch字段为4、397B为1，与 Strict constraint: Batch=1 注释不一致，需从实际输入/执行器验收，不自动改成统一batch。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/qwen3_5/qwen3_5_moe_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/models/modeling_qwen3_5_moe.py)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_35b_ep8.yaml)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_122b_tp8.yaml)
- [固定来源 6](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/qwen3_5/config/qwen3_5_397b_tp16.yaml)
