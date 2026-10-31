---
type: Optimization
title: LongCat-Lite A3 EP 量化与多流来源观测
description: 最新来源明确A3 EP8下的W8A8与多流/控核结果；更新已解决SP代码缺口，保留测量和质量限制。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
  role: implementation
created_at: '2026-10-21T09:56:24Z'
updated_at: '2026-10-29T13:59:24Z'
platforms:
- a3
---

# LongCat-Lite A3 EP、量化与多流来源观测

## 当前证据范围

最新EP报告明确将以下量化和多流结果绑定Atlas A3、EP8；旧稿无法绑定平台的Prolog/SP历史点已撤下。当前源码也已包含is_sp与RS+AG，旧“源码未实现SP”的缺口已解决。

## Workload 与 Result

| 对照 | 条件 | 来源报告 |
| --- | --- | --- |
| BF16→W8A8 | batch2，1K输入/128输出 | Decode 8.38→7.18ms |
| BF16→W8A8 | batch8，4K输入/1K输出 | Decode 9.80→8.21ms |
| W8A8串行→多流+控核 | EP8，batch8，约4K/1K | 端到端8.21→7.12ms；设备侧7.67→6.62ms |

量化只覆盖MoE/Dense，MLA仍BF16。多流整段MoE与另一子层重叠，包含控核，不能归因于只切流。README最终吞吐1124tok/s对应其GBS8、TPOT7.12ms的报告值；不与其他batch/TP路径混比。

## Metric、Software 与限制

源报告区分设备侧与端到端，并说明主机负载会改变后者；未公开完整测量脚本、逐轮样本、方差或每行软件build。短16步logits cosine/top1对齐不是完整任务精度证明。本次未运行模型，来源结果不设为verified。

复现须分别核对平台、GE多流路径、真实量化、输入、重复统计与任务精度；步骤见[当前部署](../../guides/models/longcat_flash_lite_deployment.md)。


## Evidence

- [optimization_report_ep.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_ep.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)（supporting）
- [modeling_longcat_flash_lite.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)（implementation）
