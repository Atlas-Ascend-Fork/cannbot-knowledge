---
type: Optimization
title: Sana-Video 950 量化来源观测
description: 当前README的480p81f来源结果与测量缺口；不将合并平台表、默认配置或混合位宽误作完整对照。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md
  role: primary
created_at: '2026-10-21T09:56:25Z'
updated_at: '2026-10-29T14:16:27Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
---

# Sana-Video 950来源量化性能观测

## Workload

480p81f、单卡；BF16/a8w8/a4w4在同一来源表内列出，采样配置及实际输出质量未完整披露。

## Hardware

当前README直接标Atlas 950；不把相邻A2/A3的BF16行移入本表。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 量化方式 | 规格 | 单步时延(s) | Diffusion sampling(s) | 整网耗时(s) |
| ---- | ---- | ---- | ---- | ---- |
| bf16 | 480p81f | 1.67 | 83.5 | 90.44 |
| 8bit (a8w8) | 480p81f | 1.46 | 73 | 79.38 |
| 4bit (a4w4) | 480p81f | 1.43 | 71.5 | 77.92 |

## Limitations 与验证

a4w4模式部分层仍a8w8，不填量化OR Scope。不从端到端数字推断所有层都支持同一精度、也不把该表外推到A2/A3。

复现与回退入口：[模型部署与验收流程](../../guides/models/sana_video_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md)（primary）
