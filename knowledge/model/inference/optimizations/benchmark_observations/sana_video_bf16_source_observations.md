---
type: Optimization
title: Sana-Video 480p81f 来源时延（平台与精度待核验）
description: 保留来源中 A2/A3 合并表的 480p81f 单步和采样时延；表内未绑定具体卡型或 quant_type，不将默认 BF16 配置当作测量精度证据。
tags:
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md
  role: primary
created_at: '2026-10-21T09:56:26Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# Sana-Video 480p81f 来源时延（平台与精度待核验）

## Workload

源 README 的 480p81f 时延记录；只有单步与 Diffusion sampling 值，表内没有标注 quant_type。

## Hardware

源用Atlas A2/A3合并表名，未区分下面一行是哪一平台的测量；不声称两平台分别测得相同结果。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 来源平台表名 | 规格 | 单步时延(s) | Diffusion sampling(s) |
| --- | --- | --- | --- |
| Atlas A2/A3（未细分） | 480p81f | 2.75 | 132 |


## Limitations 与验证

缺具体卡型、测量精度、完整输入输出与测量记录，保留 draft 与未知平台；不以此作为 950 量化表的共同 baseline。

复现与回退入口：[模型部署与验收流程](../../guides/models/sana_video_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md)

## 本轮来源核对与剩余缺口

固定 README 的合并表标题明确写 A2/A3，但 2.75s/132s 一行没有分别列出平台，也没有精度列。部署 YAML 示例的 quant_type=bf16 是默认配置说明，不足以证明该行的实际测量精度；因此撤下标题和 Workload 中的 BF16 确认。132/2.75 的比值也不能替代来源未披露的步数或计时边界。
