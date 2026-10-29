---
type: Optimization
title: LongCat-Lite A3 MLA-Prolog 与长输入的来源观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md
  role: primary
created_at: '2026-10-21T09:56:24Z'
updated_at: '2026-10-21T09:56:24Z'
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

# LongCat-Lite A3 MLA-Prolog 与长输入的来源观测

## Workload

TP8、BF16、batch1；短输入1024/输出128，长输入4096/输出1024；按报告稳态口径。

## Hardware

Atlas A3；不使用EP报告未定位平台的数字。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 路径/输入 | Prefill(ms) | Decode(ms/token) | 吞吐(tok/s) |
| --- | --- | --- | --- |
| Ngram已入图，未启Prolog，1K/128 | ~62 | 5.86 | ~170 |
| 启Prolog，1K/128 | ~62 | 5.49 | ~182 |
| 启Prolog，4K/1K | 216.5 | 6.00 | ~167 |

源报告约6% Prolog增益；长输入行同时改变输入/输出长度，不能归因为一个参数。图外/入图阶段数据继续由既有入图案例维护。


## Limitations 与验证

源在Prolog阶段记录约第8个token起出现分歧，不能把作者“语义等价”解释为精度通过。两阶段回退需匹配相应配置和cache。

复现与回退入口：[模型部署与验收流程](../../guides/models/longcat_flash_lite_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_tp.md)
