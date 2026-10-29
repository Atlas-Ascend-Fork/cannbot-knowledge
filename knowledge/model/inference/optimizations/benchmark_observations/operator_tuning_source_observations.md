---
type: Optimization
title: LI/DIA PyPTO 调优的来源观测（测量条件待补）
description: 保留 PyPTO LI 的三项调优披露与 DIA 首版瓶颈比例，目标库支持 A3，但逐次测量环境仍待补。
tags:
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/pypto/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/pypto/docs/lightning_indexer.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/pypto/docs/deepseek_indexer_attention.md
  role: supporting
created_at: '2026-10-22T01:42:26Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# LI/DIA PyPTO 调优的来源观测（测量条件待补）

## Workload

LI 泳道调优说明为 4 batch、64K；DIA 首版 Gather 比例是另一组披露，不共享测量条件。

## Hardware

同提交 PyPTO 库及接口文档明确目标为 Atlas A3；这确认库的支持范围，尚不能独立确认下面各次测量的实际卡型。保留 draft、空平台，不把支持矩阵当作测量日志。

## Software

固定 2f82d10467e6fe8dae81c97a2cdac78d733a6703 指南。逐测点 CANN、torch_npu 和编译 build 未完整披露。

## Baseline 与 Variant

LI 对比 Pass 修复及 Vector tile 调整前后；DIA 仅提供首版瓶颈占比。

## Metric Definition

相对提升沿用来源口径；缺少完整计时资料时不改写为端到端性能。

## Repetition and Variance

缺 warmup、重复测量与方差，本仓未独立复测。

## Result

### LI PyPTO 的三项披露


| 来源措施 | 来源报告 |
| --- | --- |
| Pass 泛化能力修复 | +10% |
| Vector tile 调为 {64,256} | +17% |
| 综合调优 | +27% |

不将两个百分比直接相加作为独立推导，也不据此保证其他形状获益。


### DIA 首版泳道的瓶颈披露


V3.2-Exp PyPTO 指南另称首版 DIA 的离散 Gather 耗时占比超过 70%。原始样本、测量环境和与其他表的对应关系不足，不把该比例推广到所有 DIA 实现或负载。


## Limitations 与验证

补齐实际测量环境、输入、命令、计时口径、精度和多轮样本后再评审；只确认支持平台不自动关闭实验缺口。A3 的 AscendC LI/HcPost 数据由[独立来源观测](ascendc_a3_li_hcpost_source_observations.md)维护。

## Evidence

- [固定来源](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)

## 本轮来源核对与剩余缺口

同提交库 README 与 LI/DIA 接口支持表明确为 Atlas A3，现已补入来源；它们确认的是实现支持范围。LI 的 +10%/+17%/+27% 与 DIA 的 Gather>70% 尚缺实际执行卡型、完整命令和样本，不能由库支持表代替测量记录。按用户确认，直接绑定 A3 的 AscendC LI 与 HcPost 数据已迁入独立来源观测，原数字未丢失。
