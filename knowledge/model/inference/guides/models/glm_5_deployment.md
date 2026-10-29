---
type: Guide
title: GLM-5 A3 部署、量化与 DSA 验收流程
description: GLM-5 A3 部署、量化与 DSA 验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/modeling_glm.py
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-21T09:56:17Z'
platforms:
- a3
---

# GLM-5 A3 部署、量化与 DSA 验收流程

## 目标、输入与产物

面向固定来源中的 GLM-5 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/glm_5.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 固定权重与环境

按固定 README 核对 Atlas A3、镜像与驱动，FP8 权重经 `utils/weight_convert.sh --quant_mode w8a8c16` 转换为本 benchmark 的 W8A8C16；脚本接受其他模式不代表这些模式都完成 GLM-5 评测。转换前后路径分开保存。

## 2. 配置阶段与通信域

部署 YAML 均 `exe_mode: ge_graph`（[npu-graph-mode](../../concepts/techniques/npu_graph_mode.md)），`world_size = 2 × chip_num`。Int8 Prefill / Decode 均支持 **8-128 卡**（README）。

| 阶段 | YAML | world_size | cp_size | attn_tp | oproj_tp | dense_tp | moe_tp | embed/lmhead_tp | batch | input_max_len |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| Prefill | `glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml` | 64 | 64 | 1 | 1 | 1 | 1 | 16 | 64 | 65536 |
| Decode | `glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml` | 128 | 128 | 1 | 4 | 4 | 1 | 16 | 256 | 65536 |

- **CP（长序列）**：`cp_size` 仅 Prefill 生效且 `cp_size = world_size`（长序列 65536，数据集 InfiniteBench `longbook_qa_eng`）；Decode 不启 CP。多 rank 均摊长序列 Attention 计算降低 TTFT，机理见 [context-parallel](../../concepts/parallelism/context_parallel.md)。
- **Attention DP**：`attn_tp_size=1` 即 attention 数据并行；`oproj_tp_size` 独立切（仅 `attn_tp_size==1` 时支持）——Decode 取 `oproj_tp 4 / dense_tp 4`，Prefill 取 1。
- **Embed / LMHead TP**：`embed_tp_size = lmhead_tp_size = 16`（A3 单 node 8 卡 × 2 die = 16，TP 域控制在 HCCS 内）。
- **MoE EP**：64ep（Prefill）/ 128ep（Decode），`moe_tp_size=1`。
- **其它**：`enable_weight_nz: True`、`pa_block_size: 128`（见 [weight-nz](../../concepts/techniques/weight_nz.md)）、`enable_multi_streams: True`、`enable_online_split_weight: True`、`perfect_eplb` 可选。

配置表数值只适用于所列固定 YAML，world_size 与物理卡单位另行核对。CP 原则读取 [整域 CP 案例](../../optimizations/cases/deepseek_kimi_a3_prefill_cp.md)，投影 TP 读取 [局部 TP 规则](../../optimizations/rules/local_tp_memory_heavy_projections.md)。

## 3. 逐条核对 GLM 实现差异

DSA 路径为 MLAProlog→Absorb/Prefill CP 分支→SFA。EP Decode 使用独立 `moe_ep_group_mc2` 与 `fullmesh_v2`，Prefill 用 double-routing；不要把 V3.2 的超参或全部默认值套到 GLM。`enable_multi_streams` 的 shared/routed expert 分支按 [多流流程](../../guides/optimization/multi_stream_optimization_workflow.md)验收同步与收益。

MoE 的 w8a8int8/w4a8int4 分支、npu_dequant_swiglu_quant 与非量化 npu_swiglu 分开核对。两份 benchmark YAML 的 next_n=3 与 perfect EPLB 为来源性能前提；后者不用于最终精度验收。MTP 接入见 [MTP 流程](../../guides/integration/mtp_speculative_decode_model_onboarding.md)，Host Offload 见 [Offload 流程](../../optimizations/rules/kvcache_offload_host_swap.md)。

## 4. 启动与结果

按 README 同步修改节点 IP、CANN 路径、model_path 和 infer.sh 的 YAML_FILE_NAME，再在各节点运行固定入口。HCCL_BUFFSIZE 报错按 [通信缓冲诊断](../../runbooks/runtime/hccl_buffsize_too_small.md)处理，各 rank 取一致值；不要用吞吐表反推正确配置。来源数据统一在 [GLM-5 A3 观测](../../optimizations/benchmark_observations/glm5_a3_source_benchmark.md)。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/README.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/modeling_glm.py)
