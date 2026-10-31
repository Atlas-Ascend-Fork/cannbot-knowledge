---
type: Guide
title: DeepSeek-R1 A3 分阶段部署与优化验收流程
description: 更新R1当前A3软件、统一入口和配置字段，区分普通/长序列MTP与人工EPLB基准，并核对packed Prefill预算。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml
  role: supporting
created_at: '2026-10-21T09:56:16Z'
updated_at: '2026-10-29T15:03:47Z'
platforms:
- a3
---

# DeepSeek-R1 A3 分阶段部署与优化验收流程

## 目标、输入与产物

面向固定来源中的 DeepSeek-R1 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/deepseek_r1.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 当前环境和启动

README要求A3、CANN9.0.0、PyTorch2.8.0、torch_npu2.8.0.post4（扩展v26.0.0）、Python3.11。各节点设置IP/CANN环境并安装模型requirements；同目录Kimi-K2（非Thinking）还要求transformers4.55.0。源FP8权重先在模型目录转换为目标精度，W8A8C8转换只为R1提供。

从仓根执行，例如：

```bash
bash executor/scripts/infer.sh --model deepseek_r1 --yaml decode_r1_rank_16_16ep_a8w8.yaml
```

各节点分别启动，模型res目录保存日志；在线PD使用--mode online和P/D配置。简单输入可用default，长文本数据按README准备LongBench/InfiniteBench。

## 1. 确认权重与执行器

使用 `models/deepseek_r1/` 的自研执行器路径，保存权重格式并按 `utils/weight_convert.sh` 选择 bfloat16、w8a8c16 或 R1 的 w8a8c8 路径。Kimi-K2-Thinking已接统一Executor但保留独立建模适配，不能因架构同族而直接复用文件或全部开关。转换选择见 [权重转换流程](../../guides/deployment/quant_weight_conversion_path_selection.md)。

## 2. 选择阶段配置

根据 `config/*.yaml` 实际提供的部署方案：

| 阶段 | 配置文件 | world_size | 并行 | 量化 | 备注 |
| ---- | ------- | ---------- | ---- | ---- | ---- |
| Prefill | `prefill_r1_rank_32_32dp_32ep_a8w8.yaml` | 32 | MLA-DP32 + MoE-EP32 | W8A8 | `micro_batch_mode: 1`（DP+EP），`moe_chunk_max_len: 65536` |
| Decode | `decode_r1_rank_16_16ep_a8w8.yaml` | 16 | MLA-DP16 + MoE-EP16 | W8A8 | `npugraph_ex`（ACL Graph 图模式），无 MTP，小规模/调试用 |
| Decode | `decode_r1_rank_16_16tp_a8w8.yaml` | 16 | MLA-TP16 + MoE-TP16 | W8A8 | `moe_tp_size > 1`，走 `moe_infer_tp` 路径 |
| Decode | `decode_r1_rank_128_128ep_a8w8.yaml` | 128 | MLA-DP128 + MoE-EP128 | W8A8 | `ge_graph`，大 EP 部署 |
| Decode | `decode_r1_rank_128_128ep_a8w8c8_mtp.yaml` | 128 | DP128 + EP128 | **W8A8C8** | next_n: 1（MTP1），enable_superkernel: False（此样例关闭） |
| Decode | `decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml` | 128 | DP128 + EP128 | W8A8C8 | Benchmark 配置，`force_eplb: True`、`max_prefill_tokens: 4096` |
| Decode | `decode_r1_rank_128_128ep_a8w8c8_mtp_longseq.yaml` | 128 | DP128 + EP128 | W8A8C8 | next_n=3、batch256、moe_chunk_max_len=512 |

> `attn_tp_size=1` 不对Attention头做TP；`moe_tp_size=1`时仍需核对EP组和专家分片，不能称每卡持有完整MoE权重。Embedding/LMHead的TP分别看实际字段。

`world_size`、进程/rank、die 和物理卡必须从实际拓扑核对；不依据world_size单独换算机器或物理卡数。路由专家与shared expert的权重部署分别核对。

## 3. 按已有入口选择优化

| 阶段与任务 | 规范入口与本模型差异 |
| --- | --- |
| Prefill DP / SP-TP-SP | [MLA 切分规则](../../optimizations/rules/prefill_mla_dp_vs_sp_tp_sp_parallel.md)；按请求分布和 KV 预算选择，不由卡数机械推导 |
| Prefill 双流 | [micro-batch 流程](../../guides/optimization/prefill_micro_batch_dual_stream_moe_overlap.md)；`micro_batch_mode` 0/1/2 分别关闭、DP+EP、SP+TP+EP；SDMA/AIV 冲突按流程处理 |
| Prefill NTD | [MLA 布局案例](../../optimizations/cases/mla_prefill_flash_attention_ntd_layout.md)；不同调用点的 NTD_TND/TND_NTD 不可混写 |
| Decode MLA / EP | [MLA-Prolog](../../concepts/kernels/mla_prolog.md)、[EP 融合机制](../../concepts/techniques/moe_dispatch_combine_v2.md)；量化模式、cache 与 HCCL 配置一起核对 |
| Decode 图、缓存、SuperKernel | [图模式决策](../../optimizations/rules/graph_mode_enable_decision_profiling.md)、[编译缓存](../../optimizations/rules/torchair_cache_compile_persisted_graph.md)、[融合范围规则](../../optimizations/rules/superkernel_decode_ge_graph_fusion_scope.md)；当前合法后端eager/ge_graph/npugraph_ex，旧acl_graph值已不适用 |
| MTP | [MTP 接入](../../guides/integration/mtp_speculative_decode_model_onboarding.md)、[计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)；`next_n`、多 token mask 和 cache 状态一并验收 |

当前开关位于model_config.custom_params，含enable_mla_prolog、enable_multi_streams、enable_superkernel、micro_batch_mode、moe_chunk_max_len、enable_o_proj_alltoall。block_size属于scheduler_config，输入长度为data_config.input_truncated_len；enable_pa/pa_block_size/input_max_len不再是当前配置入口。

## 4. 长序列内存与结果入口

KV块预算、max_prefill_tokens控制packed Prefill总prompt预算与moe_chunk_max_len切块是不同手段，逐项检查质量与吞吐代价；排障见 [MoE Prefill OOM](../../runbooks/performance/moe_prefill_oom_peak_memory.md)。`enable_weight_nz` 的布局语义由 [weightNZ](../../concepts/techniques/weight_nz.md)维护。

性能表集中在 [Prefill 观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)与[Decode 观测](../../optimizations/benchmark_observations/deepseek_r1_a3_decode_source_benchmark.md)，当前两份来源均标64 Chips；不能从world_size另推物理卡数。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md)（primary）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（primary）
- [deepseek_r1_decode_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [decode_r1_rank_128_128ep_a8w8c8_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp.yaml)（supporting）
- [decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml)（supporting）
