---
type: Optimization
title: DeepSeek-V3.2-Exp A3 时延、吞吐与容量的来源观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
created_at: '2026-10-21T09:56:22Z'
updated_at: '2026-10-21T09:56:22Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      - prefill
---

# DeepSeek-V3.2-Exp A3 时延、吞吐与容量的来源观测

## Workload

固定指南的BF16/W8A8C8、MoE W4A8与Offload记录；表内MTP3及perfect EPLB，平均3个draft接受1.44个。

## Hardware

Atlas A3，Chips沿原表16/32/64，不用world_size代替。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

### W8A8C8，未开Offload

| Global Batch Size | Seq Length | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- |
| 256 | 65536 | 64 | 19.84 | 202 |
| 512 | 65536 | 64 | 22.78 | 351 |
| 128 | 131072 | 64 | 18.85 | 106 |
| 512 | 131072 | 64 | 25.8 | 310 |

### MoE W4A8 / W8A8对比

| MoE Quant Mode | Global Batch Size | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- |
| W8A8 | 64 | 32 | 20.81 | 96 |
| W4A8 | 64 | 32 | 20.18 | 99 |
| W8A8 | 32 | 16 | 24.39 | 82 |
| W4A8 | 32 | 16 | 22.51 | 89 |

第二组共同序列长度65536，MTP及其他配置按原文引用第一组；不能由该几行推出权重越大收益必然单调增加。

### 其他来源声明

来源概述称64卡128K BF16 TTFT<2s、TPOT<30ms，W8A8C8 TPOT<20ms；吞吐曲线称128K相对V3.1达到450%。这些概述/图示声明缺少对应原始记录，不替代上表逐行条件。

Offload容量图称固定64K时global batch1024→2048，固定batch128时长度256K→384K，前提仍为MTP3及perfect EPLB。容量提升不等于同一请求的时延下降。


## Limitations 与验证

质量表由[精度草稿](../../optimizations/benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)维护；本卡仅记录性能和容量。结果覆盖多个分支，不写混合量化OR条件，也不将来源摘要当作统一SLA。

复现与回退入口：[模型部署与验收流程](../../guides/models/deepseek_v3_2_exp_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)
