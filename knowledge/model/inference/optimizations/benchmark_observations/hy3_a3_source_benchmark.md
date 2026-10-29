---
type: Optimization
title: Hy3-preview A3 分阶段性能与批次口径观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/optimization_report.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/README.md
created_at: '2026-10-21T09:56:23Z'
updated_at: '2026-10-22T10:39:39Z'
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

# Hy3-preview A3 分阶段性能与批次口径观测

## Workload

BF16，eager→GE/SuperKernel/cache演进；Prefill1024token。来源基线batch4，最终配置batch16，且配置截断400/输出112与部分报告32token记录不同。

## Hardware

Atlas A3，来源明示16die（8卡×2die），64GB HBM/die；来源基线 BF16 部署显存占用约54.5GB/die。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 来源阶段 | Decode(ms/token) |
| --- | --- |
| 初始eager | 293 |
| SuperKernel阶段 | 30.8 |
| 最终重编译，2026-04-28 | 28.44 |

最终记录写range27.4–29.4、32tokens。源给9.5×/10.3×阶段比值，原始逐轮记录未提供，不能当作同一次重测的两个可互换结果。

Prefill基线2070ms（batch4）和最终1452ms（batch16）不可直接相除得出速度提升。版本前提也不同：README列CANN9.0.0，报告SuperKernel限制取8.5.0，不擅合并。


## Limitations 与验证

原文以正常文本解释质量，未给充分任务精度；sigmoid/bias语义差异须另验。保留阶段值与环境分歧，不将30.8/28.44合并为一个当前保证。

复现与回退入口：[模型部署与验收流程](../../guides/models/hy3_preview_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/optimization_report.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hy3_preview/README.md)
