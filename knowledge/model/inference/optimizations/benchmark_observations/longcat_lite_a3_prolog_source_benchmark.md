---
type: Optimization
title: LongCat-Lite A3 MLA-Prolog 与长输入的来源观测
description: 当前TP报告的A3 5.76ms与4K长输入6.00ms来源结果，区分Prolog实验、稳态和质量边界。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md
  role: supporting
created_at: '2026-10-21T09:56:24Z'
updated_at: '2026-10-29T13:59:24Z'
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

# LongCat-Lite A3 TP 与长输入来源观测

## Workload 与 Hardware

当前TP报告的Atlas A3、TP8、BF16、batch1；短输入1024/输出128，长输入4096/输出1024。以下均为来源报告，未在本次复测。

## Result

| 条件 | Prefill ms | Decode ms/token | 吞吐 tok/s |
| --- | --- | --- | --- |
| 当前报告A3最终路径，1K/128 | 47.84 | 5.76 | 174 |
| 当前报告长输入，4K/1K | 216.5 | 6.00 | 约167 |

报告另称同代码关闭Prolog约6.1ms，对比当前5.76ms约5–6%；该历史实验开关不等于当前模型仍暴露相同flag。旧62ms/5.49ms阶段数据不再作为本卡当前结果。

## Software、Metric 与限制

当前来源保留阶段性实验数据，未提供每行完整软件build、原始样本、重复次数或方差。上表是稳态口径，不能当冷启动或在线服务端到端值；长输入行同时改变输入/输出长度。

报告承认约20 token后输出分歧，作者的语义判断不代替任务精度验收。实际部署按[当前指南](../../guides/models/longcat_flash_lite_deployment.md)重新验证，未增加verified。


## Evidence

- [optimization_report_tp.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/agentic/optimization_report_tp.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash_lite/README.md)（supporting）
