---
type: Optimization
title: Gemma-4 A2 当前来源性能与累计阶段
description: 最新Gemma A2累计PA/FIA阶段与GE表分开，撤下已不在当前报告的旧18.21ms值。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/config/gemma4_rank_8_8ep_decode.yaml
  role: example
created_at: '2026-10-21T09:56:22Z'
updated_at: '2026-10-29T14:25:50Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      - prefill
---

# Gemma-4 A2 当前来源性能与累计阶段

## Workload、Hardware 与 Software

来源为最新README和报告：A2八卡、BF16、batch8、输入256，README基线输出32。报告含累计阶段表与GE后端表，两组记录分开，不平均。当前安装说明CANN9.0.0不自动证明每阶段测量采用同一build。

## Result

| 来源组 | 条件 | Prefill ms | Decode ms/step |
| --- | --- | --- | --- |
| 报告基线 | eager | 312.51 | 98.47 |
| 累计表 | 并行切分 | 313 | 97 |
| 累计表 | 融合算子 | 307 | 92 |
| 累计表 | PA + FIA v2 | 303 | 11.4 |
| 累计表 | Sliding融合RoPE/MC2阶段 | 303 | 11.1 |
| GE后端表 | GE Decode、Prefill eager | 189 | 15.0 |

最新报告已重写累计表，旧302.52/18.21ms记录不再出现在当前来源，已撤下。累计11.1ms与GE表15ms缺少逐轮记录解释，不能拼成同一受控实验；也不把Prefill变化归因于Decode编图。

## Metric、Repetition 与限制

数据单位沿来源，缺每行完整build、运行命令、逐轮样本和方差。README给A2 GE吞吐533tok/s，属于其batch/TPOT口径，不能改为在线服务吞吐。报告精度基线要求token一致，但本次未复测当前PA/RoPE实现。

复现见[当前指南](../../guides/models/gemma4_26b_a4b_deployment.md)，另与[A3观测](gemma4_a3_source_benchmark.md)区分。来源自报不新增verified。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/README.md)（primary）
- [modeling_gemma4.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py)（implementation）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md)（supporting）
- [gemma4_rank_8_8ep_decode.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/config/gemma4_rank_8_8ep_decode.yaml)（example）
