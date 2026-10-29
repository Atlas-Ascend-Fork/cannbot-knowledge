---
type: Optimization
title: Gemma-4 A2 图模式的两组来源性能口径
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md
  role: primary
created_at: '2026-10-21T09:56:22Z'
updated_at: '2026-10-21T09:56:22Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      - prefill
---

# Gemma-4 A2 图模式的两组来源性能口径

## Workload

BF16、EP8、batch8，来源测试条件seq256；max_new_tokens32见路由/跨硬件上下文，不补为每行完整生成记录。

## Hardware

Atlas A2，8卡；两组A2值分开保存。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 来源组 | 路径 | Prefill(ms) | Decode(ms/token) |
| --- | --- | --- | --- |
| 累计/§6.1 | eager baseline | 312.51 | 98.47 |
| 累计/§6.1 | GE | 302.52 | 18.21 |
| 跨硬件/§7 | eager | 312.5 | 98.5 |
| 跨硬件/§7 | GE | 189 | 15 |

原文累计表称约5.42×；两组GE值没有足够记录解释差异，不平均，不与A3行拼成单一实验。

## Limitations 与验证

GE Decode手工GEGLU与eager可能不bit-exact；原文“语义一致”只是作者判断。跨平台对比另读[A3观测](../../optimizations/benchmark_observations/gemma4_a3_source_benchmark.md)，不能用本卡累计组冒充其A2基线。

复现与回退入口：[模型部署与验收流程](../../guides/models/gemma4_26b_a4b_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md)
