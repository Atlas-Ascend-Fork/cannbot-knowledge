---
type: Optimization
title: Qwen3-MoE A3 两条实现的来源时延观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_moe/qwen3_moe_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/README.md
  role: supporting
created_at: '2026-10-21T09:56:24Z'
updated_at: '2026-10-29T13:54:05Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# Qwen3-MoE A3 两条实现的来源时延观测

## Workload

自研概述未明确模型规格；其BF16单batch与SGLang Qwen3-235B-A22B W8A8为不同记录，没有匹配的共同baseline。

## Hardware

两者来源均指A3；自研概述8卡，SGLang32卡，不把两种模型运行条件拼接。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 来源路径 | 条件 | 原指标 |
| --- | --- | --- |
| 自研优化文档概述 | BF16，8卡，单batch；输入/完整YAML未披露 | 推理时延<20ms |
| SGLang README | Qwen3-235B-A22B，W8A8，GBS256，dp16/tp4/ep64，max_prompt5120/max_response500，32卡 | 纯模型时延30ms |

SGLang来源开启SuperKernel、perfect EPLB与cache compile；“纯模型时延”不替换为在线端到端时延，源概述不补写成逐token样本。

## Limitations 与验证

量化/框架/并行/batch不同，不能由20与30ms直接选出更优实现。机器Scope只标来源明确的Decode，其他条件仍需读相应行确认。

复现与回退入口：[模型部署与验收流程](../../guides/models/qwen3_moe_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [qwen3_moe_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_moe/qwen3_moe_optimization.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/README.md)（supporting）
