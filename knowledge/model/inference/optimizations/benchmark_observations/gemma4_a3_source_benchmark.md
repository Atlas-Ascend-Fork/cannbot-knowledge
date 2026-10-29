---
type: Optimization
title: Gemma-4 A3 图后端与 EP 路由的来源观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md
  role: primary
created_at: '2026-10-21T09:56:23Z'
updated_at: '2026-10-21T09:56:23Z'
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

# Gemma-4 A3 图后端与 EP 路由的来源观测

## Workload

BF16、EP8、batch8、input_len256、max_new_tokens32；按后端与路由模式分组。

## Hardware

Atlas A3，8卡。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 路径/来源组 | Prefill(ms) | Decode(ms/token) |
| --- | --- | --- |
| GE + local_experts，§6.3 | 76 | 10.20 |
| GE + mc2，§6.3 | 77 | 10.50 |
| npugraph_ex + local_experts，§6.3 | 102 | 11.59 |
| npugraph_ex + mc2，§6.3 | 112 | 11.73 |
| GE，跨硬件§7 | 76.43 | 10.20 |
| npugraph_ex，跨硬件§7 | 102.29 | 11.59 |

源另给首次GE编译8.38s/605s、npugraph_ex7.18s/358s（Prefill/Decode列），不与稳态时延相加或当作重复测量。源称两路由输出一致，只限该来源工况。

## Limitations 与验证

大batch/Prefill的mc2相对优势未由本组小batch数字验证，不写普遍选择规则。源码默认mc2与YAML显式local_experts不同，以生效配置为准。A2的两组数据另见[A2观测](../../optimizations/benchmark_observations/gemma4_a2_source_benchmark.md)。

复现与回退入口：[模型部署与验收流程](../../guides/models/gemma4_26b_a4b_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/gemma4_26b_a4b/agentic/optimization_report.md)
