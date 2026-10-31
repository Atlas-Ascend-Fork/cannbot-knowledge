---
type: Optimization
title: Gemma-4 A3 当前图后端来源观测
description: 最新Gemma A3 GE/npugraph来源表和吞吐，撤下已删除local_experts配置及不再存在的旧编译表。
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
created_at: '2026-10-21T09:56:23Z'
updated_at: '2026-10-29T14:25:50Z'
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

# Gemma-4 A3 当前图后端来源观测

## Workload、Hardware 与 Software

当前来源A3八卡、BF16、MoE EP8、batch8、输入256/输出32。README与优化报告共同绑定图后端；安装说明CANN9.0.0/PyTorch2.8.0不代替逐行完整测量build。

## Result

| 后端 | 报告Prefill ms | 报告Decode ms/step | README吞吐tok/s |
| --- | --- | --- | --- |
| GE | 76.43 | 10.20 | 784 |
| npugraph_ex | 102.29 | 11.59 | 690 |

README Decode分别四舍五入为10.2/11.6ms，未视为新实验。两组仅Decode编图，Prefill保持eager；不能将Prefill差异归因于Prefill图编译。

旧local_experts/MC2消融与首次编译8.38s/605s等表已不在当前报告，且local_experts实现已删除，已从当前观测撤下。报告仍概述缓存二次warmup约省20倍，缺完整原始记录，不能推广为任意启动收益。

## Metric、Repetition 与限制

缺逐轮样本、方差、完整命令和质量结果，作者基线精度判断不等于目标build验证。当前实际GEGLU与报告文字存在差异，应按代码验输出。不同硬件记录另见[A2观测](gemma4_a2_source_benchmark.md)，本次未运行NPU，也未新增verified。

复现和回退见[当前部署](../../guides/models/gemma4_26b_a4b_deployment.md)。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/README.md)（primary）
- [modeling_gemma4.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/models/modeling_gemma4.py)（implementation）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/agentic/optimization_report.md)（supporting）
- [gemma4_rank_8_8ep_decode.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/gemma_4/config/gemma4_rank_8_8ep_decode.yaml)（example）
