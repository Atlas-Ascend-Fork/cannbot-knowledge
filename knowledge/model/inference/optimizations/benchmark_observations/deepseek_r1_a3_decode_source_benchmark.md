---
type: Optimization
title: DeepSeek-R1 A3 Decode 的来源数据与 Chips 分歧
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml
created_at: '2026-10-21T09:56:22Z'
updated_at: '2026-10-21T09:56:22Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# DeepSeek-R1 A3 Decode 的来源数据与 Chips 分歧

## Workload

W8A8C8，Global Batch6144，Seq Length4096；MTP1、perfect EPLB，来源平均每1个draft接受0.7个。

## Hardware

Atlas A3；Decode优化文档Chips=128，而README同组值Chips=64。world_size=128不是单独裁决物理卡数的证据。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 来源 | Quant Mode | Global Batch | Seq Length | Chips（原标注） | TPOT(ms) | Throughput(tokens/p/s) |
| --- | --- | --- | --- | --- | --- | --- |
| Decode优化文档 | W8A8C8 | 6144 | 4096 | 128 | 44.9 | 2138 |
| 模型README | W8A8C8 | 6144 | 4096 | 64 | 44.9 | 2138 |

这两行保留来源分歧，不当作两次独立实验，也不选择其中一个作为已确认卡数。

## Limitations 与验证

硬件单位、吞吐分母和完整日志仍需补证。MTP接受数与perfect EPLB不是精度保证，无法据这张表对其他并行规模外推收益。

复现与回退入口：[模型部署与验收流程](../../guides/models/deepseek_r1_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-r1/deepseek_r1_decode_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/README.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml)
