---
type: Optimization
title: HunyuanVideo 950PR 量化的来源性能表
description: 当前950PR量化来源表，标明MXFP8实现与offload对照因素，保留单卡/八卡独立baseline。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single.yaml
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single_fp8.yaml
  role: constraint
created_at: '2026-10-21T09:56:25Z'
updated_at: '2026-10-29T14:13:05Z'
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

# HunyuanVideo 950PR 量化的来源性能表

## Workload

来源950PR的HunyuanVideo记录，单卡与Ulysses8两组baseline分开；720p129帧条件见既有量化案例固定来源。

## Hardware

950PR；注册platform使用950，不与A3累计表共用baseline。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 并行 | 融合算子 | matmul 量化 | fa 量化 | vae 并行 | dit(s) | vae(s) | e2e | dit speedup | vae speedup | e2e speedup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1, **baseline** | √ | x | x | x | 2548.49 | 31.76 | 2580.87 | 1.00 | 1.00 | 1.00 |
| | √ | √ | x | x | 2392.24 | 31.71 | 2424.52 | 1.07 | 1.00 | 1.06 |
| | √ | x | √ | x | 1606.29 | 31.70 | 1638.55 | 1.59 | 1.00 | 1.58 |
| | √ | √ | √ | x | 1539.24 | 31.43 | 1571.24 | 1.66 | 1.01 | 1.64 |
| ulysses8, **baseline** | √ | x | x | √ | 246.29 | 10.27 | 256.92 | 1.00 | 1.00 | 1.00 |
| | √ | √ | x | √ | 231.55 | 10.33 | 244.47 | 1.06 | 0.99 | 1.05 |
| | √ | x | √ | √ | 181.85 | 10.50 | 193.96 | 1.35 | 0.98 | 1.32 |
| | √ | √ | √ | √ | 170.04 | 10.17 | 185.54 | 1.45 | 1.01 | **1.38** |

## Limitations 与验证

FA量化与Matmul量化分别看同组对照；不能把单卡baseline与Ulysses8行相除解释纯量化收益。当前实现为MXFP8 FA与A8W8；源表未给各行完整build，且single_fp8与single配置的CPU offload默认不同，复现应固定该因素。缺质量/相似度指标，不能写跨模型优先级或无损保证。

复现与回退入口：[模型部署与验收流程](../../guides/models/hunyuan_video_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（primary）
- [single.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single.yaml)（constraint）
- [single_fp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single_fp8.yaml)（constraint）
