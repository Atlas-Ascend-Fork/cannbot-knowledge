---
type: Optimization
title: HunyuanVideo A3 累计优化的来源性能观测
description: 最新来源明确默认视频规格与UAA变尺寸，保留A3累计表及非单项归因、测量缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
created_at: '2026-10-21T09:56:25Z'
updated_at: '2026-10-29T14:13:04Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
---

# HunyuanVideo A3 累计优化的来源性能观测

## Workload

当前A3累计表，baseline仅做NPU开箱FIA替换。文档现明确默认720×1280×129；UAA另测原尺寸和730×1300×129，两类标记须区分。

## Hardware

源表Atlas A3；具体芯片规格/运行记录未完整披露，不能用950结果作同一baseline。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 并行 | 融合算子 | ditcache | vae 并行 | vae 优化 | 虚拟内存<br/>取消 VAE offload | UAA | dit(s) | vae(s) | e2e | dit speedup | vae speedup | e2e speedup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1, **baseline** | x | x | x | x | x | x | 3634.48 | 133.15 | 3768.91 | 1.00 | 1.00 | 1.00 |
| | √ | x | x | √ | √ | x | 3568.36 | 39.66 | 3612.30 | 1.02 | 3.36 | 1.04 |
| | √ | FBCache | x | √ | x | x | 1693.89 | 83.03 | 1778.28 | 2.15 | 1.60 | 2.12 |
| | √ | TeaCache | x | √ | x | x | 1737.92 | 88.56 | 1830.75 | 2.09 | 1.50 | 2.06 |
| | √ | TaylorSeer | x | √ | x | x | 1405.68 | 92.85 | 1500.17 | 2.59 | 1.43 | **2.51** |
| ulysses5 | √ | x | √ | √ | √ | √ | 769.33 | 40.61 | 811.38 | 4.72 | 3.28 | 4.65 |
| ulysses8 | √ | x | √ | x | √ | x | 467.67 | 22.78 | 495.94 | 7.77 | 5.85 | 7.60 |
| | √ | x | √ | √ | √ | x | 465.43 | 12.40 | 487.68 | 7.81 | 10.74 | 7.73 |
| | √ | x | √ | √ | √ | √ | 477.12 | 13.10 | 482.65 | 7.62 | 10.16 | **7.81** |
| | √ | x | √ | √ | √ | 730, 1300 | 511.12 | 13.06 | 525.75 | 7.11 | 10.20 | 7.17 |

表内空白并行单元格沿原表保留，不自动填为新测得值；UAA“730,1300”标记的分辨率现明确为730×1300×129，仍缺逐行完整命令与原始记录。原配置称FBCache阈值0.05、TeaCache0.15、TaylorSeer算1跳3/三阶，这些是对应记录的配置，不是质量保证。


## Limitations 与验证

多优化累计结果不归因到单开关；来源没有足够画质指标证明缓存无损。模块占比81%/95%为该来源任务的profiling描述，不是模型结构常数。

复现与回退入口：[模型部署与验收流程](../../guides/models/hunyuan_video_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（primary）
