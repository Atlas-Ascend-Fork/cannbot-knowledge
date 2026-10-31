---
type: Optimization
title: DeepSeek-R1 A3 Decode 当前来源数据
description: 保留当前README与Decode指南一致的64 Chips性能记录，明确人工路由条件和测量缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml
created_at: '2026-10-21T09:56:22Z'
updated_at: '2026-10-29T15:03:47Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# DeepSeek-R1 A3 Decode 当前来源数据

## Workload

W8A8C8，Global Batch6144，Seq Length4096；MTP1、perfect EPLB，来源平均每1个draft接受0.7个。

## Hardware

Atlas A3；当前README与Decode优化指南均标Chips=64。world_size=128是rank配置，不能另外当作128物理卡。

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
| Decode优化文档 | W8A8C8 | 6144 | 4096 | 64 | 44.9 | 2138 |
| 模型README | W8A8C8 | 6144 | 4096 | 64 | 44.9 | 2138 |

当前两来源已一致。它们是同组自报数据，不当作两次独立实验；旧128标注已由来源更正，不再混列。

## 当前配置

同名benchmark YAML为world128、batch6144、next_n1、force_eplb=true、enable_superkernel=true，max_prefill_tokens4096。普通C8 MTP样例batch512且force_eplb=false、SuperKernel关闭，长序列样例next_n3；不能把本表数值归给这些不同配置。

## Limitations 与验证

硬件单位、吞吐分母和完整日志仍需补证。MTP接受数与perfect EPLB不是精度保证，无法据这张表对其他并行规模外推收益。

复现与回退入口：[模型部署与验收流程](../../guides/models/deepseek_r1_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [deepseek_r1_decode_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_decode_optimization.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/README.md)（primary）
- [decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/decode_r1_rank_128_128ep_a8w8c8_mtp_benchmark.yaml)（primary）
