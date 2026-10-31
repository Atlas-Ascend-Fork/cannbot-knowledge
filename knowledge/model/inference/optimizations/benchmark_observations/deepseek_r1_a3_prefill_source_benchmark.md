---
type: Optimization
title: DeepSeek-R1 A3 Prefill 双流的来源性能观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: primary
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
---

# DeepSeek-R1 A3 Prefill 双流的来源性能观测

## Workload

64×4K输入，来源描述2机16卡，MLA-DP32+MoE-EP32，专家均衡假设下比较micro-batch。物理卡与rank/die单位分开记录。

## Hardware

来源明确Atlas A3；2机16卡与DP32/EP32并记，不把后者擅改成32物理卡。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 切分策略 | 时延 (ms) | 总吞吐 (tokens/s) | 平均吞吐 (tokens/卡/s) |
| ---- | ---- | ---- | ---- |
| MLA-DP32 + MoE-EP32 | 3128 | 83805 | 5237 |
| + micro-batch | 2512 | 104356 | **6522** |

原优化文档自报约25%收益；perfect EPLB/负载均衡是该记录前提，不是生产输出质量结论。

## Limitations 与验证

不沿用旧总览“16与32不自洽、以32卡为准”的推断；并行单位必须由实际硬件和进程拓扑确认。不能只凭6.5k吞吐选择微批次或承诺重叠收益。

复现与回退入口：[模型部署与验收流程](../../guides/models/deepseek_r1_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)
