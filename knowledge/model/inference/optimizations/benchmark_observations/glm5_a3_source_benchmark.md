---
type: Optimization
title: GLM-5 A3 W8A8 Decode 的来源性能观测
description: 集中当前GLM-5 A3性能与新增GSM8K来源观测，明确force_eplb覆盖和评测缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml
created_at: '2026-10-21T09:56:23Z'
updated_at: '2026-10-29T15:05:36Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# GLM-5 A3 W8A8 Decode 的来源性能观测

## Workload

W8A8C16，MTP3+perfect EPLB；config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml。

## Hardware

Atlas A3，源表64 Chips；world_size128不替代物理卡单位。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| Quant Mode | Global Batch | Seq Length | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- | ---- |
| W8A8 | 256 | 65536 | 64 | 22.54 | 177.46 |

来源平均3个draft接受1.44个；未提供绑定输入及逐次测量记录。

## 当前新增精度观测

当前README还报告W8A8在GSM8K的accuracy为96.59%。未给完整权重快照、评测命令、样本/提示配置和多轮波动，不能与性能表默认视为同一次运行，也不能据此宣布无损。此平台字段来自A3样例上下文，不补造独立测量记录或verified。950配置存在不表示该分数来自950。

## Limitations 与验证

当前README称采样开启force EPLB，而所列YAML默认force_eplb=false；需补实际生效配置，不把配置默认值当作采样记录。不能用V3.2-Exp的质量或吞吐数字补齐GLM-5评测，也不能从脚本支持的其他量化模式推导它们已测得同样结果。

复现与回退入口：[模型部署与验收流程](../../guides/models/glm_5_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md)（primary）
- [glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml)（primary）
