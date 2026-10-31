---
type: Optimization
title: DeepSeek-V3.2-Exp 当前量化精度来源表
description: 只保留当前提交的量化精度表，明确BF16行原始模型标签及评测环境缺口，移除另一历史版本表。
tags:
- task.testing
- topic.performance.analysis
- topic.precision
status: draft
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md
  role: primary
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:51:46Z'
platforms: []
---

# DeepSeek-V3.2-Exp 当前量化精度来源表

当前指南保留下表；表中BF16行原文名称是DeepSeek-V3.2-BF16，量化行是V3.2-Exp，未披露足够权重/评测配置确认它们是否完全相同快照。保持draft、平台空值，不把模型部署平台当作实际评测环境。

| 来源模型标签 | MMLU | GPQA | DROP | MGSM |
| --- | ---: | ---: | ---: | ---: |
| DeepSeek-V3.2-BF16 | 90.8 | 75.85 | 87.57 | 90.9 |
| DeepSeek-V3.2-Exp-W8A8C8 | 90.62 | 75.90 | 87.41 | 90.87 |
| DeepSeek-V3.2-Exp-W4A8C8 | 90.66 | 76.5 | 87.68 | 91.3 |

按该表逐列相减，W8A8C8为-0.18/+0.05/-0.16/-0.03，W4A8C8为-0.14/+0.65/+0.11/+0.4；这些是来源表差值，不是统计显著性或量化因果收益。旧W8A8C16的另一套89.9基线已不在当前指南，本卡不再混列；历史数据保留在Git历史。

缺实际硬件、权重快照、评测命令、样本配置、重复次数和方差。来源“接近无损”的表述不能替代目标任务标准，本仓未独立复测，也不新增verified。吞吐与时延由[性能来源观测](deepseek_v32_a3_source_benchmark.md)维护。


## Evidence

- [deepseek_v3.2_exp_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_inference_guide.md)（primary）
