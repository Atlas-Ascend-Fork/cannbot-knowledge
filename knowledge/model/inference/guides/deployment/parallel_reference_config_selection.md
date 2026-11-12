---
type: Guide
title: 推理并行配置选型：按 Prefill、Decode 和模型结构找参考 YAML
description: Qwen3-MoE 16TP/128EP 与 Kimi PD Prefill/Decode 参考配置，核对 cp_size、o_proj_tp_size、R1/GLM/V3.2/LongCat YAML、DP 本地 batch
  和显存通信预算。
tags:
- task.design
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-analysis/references/config-index.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_16tp.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/config/gpt_oss_120b_8tp.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_16_16ep_a8w8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/pd/decode.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_128ep.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_16_16tp_a8w8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/config/gpt_oss_20b.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep32.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_attn4tp8dp.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_k2_rank_32_32sp_32tp_32ep_a8w8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/pd/prefill.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_longseq.yaml
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: supporting
created_at: '2026-11-09T09:23:46Z'
updated_at: '2026-11-10T04:11:13Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
aliases:
- B_local 与 DP
- DP 本地 batch
- 并行配置经验阈值
- Kimi PD 并行参数
- Kimi Prefill CP
- o_proj_tp_size
- Qwen3-MoE 并行参考
- Qwen3 16TP
- Qwen3 128EP
---

# 推理并行配置选型：按 Prefill、Decode 和模型结构找参考 YAML

## 选择方法

先固定硬件、执行器、目标阶段、模型结构、输入长度、batch 与量化格式。Decode 低时延、小规模部署可比较纯 TP；MoE 高吞吐可比较 Attention DP + MoE EP；大 dense/shared FFN 与词表投影可独立比较局部 TP。长序列 Prefill 再比较 CP 与大 TP 的计算、显存和通信成本。它们是待验证的候选，不是由模型名字决定的最优方案。

## 固定版本的可读配置

| YAML | world_size | attn_tp_size | dense_tp_size | moe_tp_size | embed_tp_size | lmhead_tp_size | o_proj_tp_size | cp_size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8.yaml | 128 | 1 | 1 | 1 | 1 | 1 | — | — |
| models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml | 128 | 1 | 1 | 1 | 1 | 1 | — | — |
| models/deepseek_r1/config/decode_r1_rank_16_16ep_a8w8.yaml | 16 | 1 | 1 | 1 | 16 | 16 | — | — |
| models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml | 128 | 1 | 4 | 1 | 16 | 16 | 8 | 128 |
| models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml | 128 | 1 | 4 | 1 | 16 | 16 | 4 | 128 |
| models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml | 128 | 1 | 4 | 1 | 16 | 16 | 4 | 128 |
| models/kimi_k2_thinking/config/pd/decode.yaml | 32 | 1 | 4 | 1 | 16 | 16 | 8 | 1 |
| models/longcat_flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml | 128 | 1 | 8 | 1 | 1 | 16 | 8 | — |
| models/qwen3_moe/config/qwen3_235b_128ep.yaml | 128 | 1 | — | 1 | 1 | 1 | — | — |
| models/deepseek_r1/config/decode_r1_rank_16_16tp_a8w8.yaml | 16 | 16 | 16 | 16 | 16 | 16 | — | — |
| models/qwen3_moe/config/qwen3_235b_16tp.yaml | 16 | 16 | — | 16 | 16 | 16 | — | — |
| models/gpt_oss/config/gpt_oss_120b_8tp.yaml | 8 | 8 | — | 8 | — | 8 | — | — |
| models/gpt_oss/config/gpt_oss_20b.yaml | 1 | 1 | — | 1 | — | 1 | — | — |
| models/longcat_flash/config/longcat_flash_densetp8_ep32.yaml | 32 | 1 | 8 | 1 | 1 | 1 | 1 | — |
| models/longcat_flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml | 32 | 1 | 8 | 1 | 1 | 1 | 8 | — |
| models/qwen3_moe/config/qwen3_235b_attn4tp8dp.yaml | 32 | 4 | — | 1 | 1 | 1 | — | — |
| models/deepseek_r1/config/prefill_k2_rank_32_32sp_32tp_32ep_a8w8.yaml | 32 | 32 | 32 | 1 | 32 | 32 | — | — |
| models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml | 32 | 1 | 1 | 1 | 32 | 32 | — | — |
| models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml | 64 | 1 | 1 | 1 | 16 | 16 | 8 | 64 |
| models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml | 64 | 1 | 1 | 1 | 16 | 16 | 1 | 64 |
| models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml | 64 | 1 | 1 | 1 | 16 | 16 | 1 | 64 |
| models/kimi_k2_thinking/config/pd/prefill.yaml | 32 | 1 | 1 | 1 | 16 | 16 | 1 | 32 |
| models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml | 128 | 1 | 4 | 1 | 16 | 16 | 4 | 128 |
| models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_longseq.yaml | 128 | 1 | 4 | 1 | 1 | 16 | — | — |


表中 world_size 表示 rank 数，不能直接当物理芯片数；A3 的具体 rank/芯片映射按部署入口核对。统一 YAML 字段为 o_proj_tp_size，代码内部属性名可能为 oproj_tp_size。读取真正的 YAML 和校验函数，再检查派生的 attn_dp_size、moe_ep_size、每 rank token 与缓存预算。

Prefill 和 Decode 常用不同配置；文件名包含 decode 也不保证 CP 在 Decode 生效。KVP 已无当前配置入口，不从历史索引恢复 kvp_size。Kimi 当前既有 kimi_k2_thinking.yaml，也保留 config/pd/prefill.yaml 和 config/pd/decode.yaml；两份 PD 配置的 CP、dense TP 与 o_proj TP 不同，不能误称其已移除，或把旧配置值套给所有入口。

表中的 `—` 只表示该 YAML 未显式填写，不能据此臆造默认值；实际值还要经过 InferenceConfig 和模型校验。表内24份文件覆盖迁出索引列出的具体 YAML 及通配候选，未把 CI 同名副本重复统计。R1 的 prefill_k2_rank_32_32sp_32tp_32ep_a8w8.yaml 是真实路径，不能按前缀猜模型目录。

## 并行推导与历史经验边界

标准非 AFD 路径中，attn_dp_size=world_size//attn_tp_size，moe_ep_size=world_size//moe_tp_size；本地 batch_size_per_dp_rank=batch_size//attn_dp_size。增加 DP 会让固定全局 batch 的本地 batch 变小，不能把“B_local 太小”解释成“DP 度不够”。AFD 会先调整有效 world_size，Prefill owner group 还有额外切分，应以配置解析后的值为准。

GQA KV 预算要计本地请求数、历史长度、层数、本地 KV 头和 dtype；MLA absorb 还要同时计 nope latent 与 rope，两类不能只按完整 K/V 投影或只计 kv_lora_rank。激活、GMM/workspace、通信预分配和布局副本另算，权重与 KV 之和不等于峰值显存。

旧并行分析中的80%/95%显存线、20%/40%通信占比线、5%/15% rank 耗时差和固定 HCCS 带宽只是未给完整负载条件的经验值，不作为通用可行性或调优阈值。多流中 Hccl Duration 之和不能直接作为 wall time 的通信占比；应看关键路径和可重叠区间。force_eplb 会覆盖真实门控路由，适合受控性能上界实验，不能作为保持模型语义的通用负载均衡修复，见[理想 EPLB 边界](../../optimizations/rules/perfect_eplb_profiling_upper_bound.md)。

## 验证与回退

核对各 TP 整除、GQA 头划分、模型专属限制及通信重排；预切权重与并行配置绑定，改拓扑后重新处理或使用正确在线切片。用相同真实权重、长度和 batch 分报 TTFT、TPOT、吞吐及显存，不能把多项优化叠加的 benchmark 当并行策略独立收益。先保持其他开关不变，只变一个拓扑候选；失败回退原配置与匹配权重。

相关：[局部 TP](../../optimizations/rules/local_tp_memory_heavy_projections.md)、[CP](../../optimizations/rules/long_seq_prefill_context_parallel.md)、[权重与通信接入](../integration/parallel_groups_and_weight_shards.md)。

## Evidence

- [.agents/skills/model-infer-parallel-analysis/references/config-index.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-parallel-analysis/references/config-index.md)
- [models/qwen3_moe/config/qwen3_235b_16tp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_16tp.yaml)
- [models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8.yaml)
- [models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml)
- [models/longcat_flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep32_gegraph_mtp.yaml)
- [models/gpt_oss/config/gpt_oss_120b_8tp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/config/gpt_oss_120b_8tp.yaml)

- [models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml)（supporting）

- [models/deepseek_r1/config/decode_r1_rank_16_16ep_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_16_16ep_a8w8.yaml)（supporting）

- [models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml)（supporting）

- [models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml)（supporting）

- [models/kimi_k2_thinking/config/pd/decode.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/pd/decode.yaml)（supporting）

- [models/longcat_flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml)（supporting）

- [models/qwen3_moe/config/qwen3_235b_128ep.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_128ep.yaml)（supporting）

- [models/deepseek_r1/config/decode_r1_rank_16_16tp_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_16_16tp_a8w8.yaml)（supporting）

- [models/gpt_oss/config/gpt_oss_20b.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gpt_oss/config/gpt_oss_20b.yaml)（supporting）

- [models/longcat_flash/config/longcat_flash_densetp8_ep32.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep32.yaml)（supporting）

- [models/qwen3_moe/config/qwen3_235b_attn4tp8dp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_attn4tp8dp.yaml)（supporting）

- [models/deepseek_r1/config/prefill_k2_rank_32_32sp_32tp_32ep_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_k2_rank_32_32sp_32tp_32ep_a8w8.yaml)（supporting）

- [models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml)（supporting）

- [models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml)（supporting）

- [models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml)（supporting）

- [models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml)（supporting）

- [models/kimi_k2_thinking/config/pd/prefill.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/config/pd/prefill.yaml)（supporting）

- [models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml)（supporting）

- [models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_longseq.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_longseq.yaml)（supporting）

- [executor/core/config/inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（supporting）
