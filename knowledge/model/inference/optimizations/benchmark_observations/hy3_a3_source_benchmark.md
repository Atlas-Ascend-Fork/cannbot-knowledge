---
type: Optimization
title: Hy3 A3 基础优化来源记录与当前配置边界
description: 最新文档保留的A3基础实验及其与当前npugraph/PA/MTP配置的边界，不混作新配置性能。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modules/common.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hy3/hy3_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/agentic/optimization_report.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_a3/hy3_rank16_bf16_mtp.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_950/hy3_rank4_mxfp4_mtp.yaml
  role: example
created_at: '2026-10-21T09:56:23Z'
updated_at: '2026-10-29T14:28:49Z'
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

# Hy3 A3 基础优化来源记录与当前配置边界

## Workload、Hardware 与 Software

最新本地agentic/optimization_report仍保留A3基础优化实验：8卡16rank、BF16，起始eager到GE/GMM/SuperKernel。报告并非当前npugraph+PA+MTP配置的测量记录，不能将其架构/开关描述直接迁移到当前部署。

## Result

| 报告阶段 | Decode ms/token |
| --- | --- |
| 初始eager | 293 |
| SuperKernel阶段 | 30.8 |
| 最终重编译 | 28.44 |

报告最终区间27.4–29.4、32tokens；基线Prefill2070ms/batch4，最终1452ms/batch16，不能直接相除归因加速。来源安装说明和阶段实际软件不同，缺完整build、原始逐轮样本与方差。

## 当前差异与限制

当前A3 ci_a3/hy3_rank16_bf16_mtp.yaml为npugraph_ex、next_n1、batch4、输入400/输出128，SP与多流关闭；模型已是packed PA和FIA v2、独立MTP。报告中的连续BSH/FA v1及MTP跳过属于其基础实验描述，已不代表当前实现。本卡保留的数值仅为当前文档内可核对的来源实验，不作为新配置性能保证。

报告声称文本正常并讨论router bias语义差异，不能证明目标任务精度或运算等价。本次未执行硬件、未新增verified；当前部署先按[指南](../../guides/models/hy3_preview_deployment.md)重新测接受率、有效token时延、质量与内存，不把MTP整步时间当每个输出token时间。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/README.md)（primary）
- [modeling_hy_v3.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py)（implementation）
- [common.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modules/common.py)（implementation）
- [hy3_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hy3/hy3_optimization.md)（supporting）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/agentic/optimization_report.md)（supporting）
- [hy3_rank16_bf16_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_a3/hy3_rank16_bf16_mtp.yaml)（example）
- [hy3_rank4_mxfp4_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_950/hy3_rank4_mxfp4_mtp.yaml)（example）
