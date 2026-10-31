---
type: Optimization
title: DeepSeek-V4 950DT混合量化的来源性能观测
description: 更新当前950DT的Flash/Pro完整来源表及HiF8混合方案，保留MTP、强制EPLB和测量缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-10-21T09:02:44Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      serving_mode:
      - offline
---


# DeepSeek-V4 950DT混合量化的来源性能观测

## Workload

当前指南自报的Offline Decode，不含Serving调度和框架负载均衡。Flash/Pro、GBS、序列、MTP及三种混合量化分别保留，当前新增HiF8方案；旧版MXFP8时延已由当前表替换，不混列为当前结果。Seq Length不自行解释为输入/输出拆分。

## Hardware

950DT，源表多数16 Chips，Pro另有64 Chips一行，Attention DP与MoE EP；不是 950PR 测量，也不把 16 Chips 自动换算为 die 或进程数。

## Software

来源固定到上述提交，但没有为这些数字给出完整的实际软件 build、测量脚本和运行日志。安装章节中的示例环境不自动等于 benchmark 环境。

## Metric Definition

TPOT 与 Throughput 沿用源表字段和单位；来源未完整说明计时起止、分母、是否含首 token，以及全部预热/统计处理。不要从标签自行补充计算公式或作为服务端到端指标。

## Repetition and Variance

来源未给 warmup、重复次数、方差/置信区间，也未公开可绑定每行数据的运行记录。本仓没有独立复测，不创建 verified。

## Baseline 与 Variant

三种 Hybrid 格式的模块配置由[混合量化机制](../../concepts/quantization/hybrid_mxfp8_mxfp4.md)维护。这里只在同规格、GBS、序列和 MTP 下比较来源结果；来源未提供完整受控试验记录。MTP 和强制 EPLB 同时参与，不能把整网结果归因给单一量化或多流开关。

## Result

| 规格 | GBS | Chips | MTP | DataType | Seq Length | TPOT(ms) | Throughput(Tokens/p/s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Flash | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 6.55 | 152.79 |
| Flash | 256 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 8.78 | 1821.75 |
| Flash | 1536 | 16 | 1 | Hybrid MXFP8-MXFP4 | 8192 | 16.46 | 5830.65 |
| Flash | 2880 | 16 | 1 | Hybrid MXFP8-MXFP4 | 8192 | 25.54 | 7047.44 |
| Flash | 256 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 9.66 | 1655.64 |
| Flash | 768 | 16 | 1 | Hybrid MXFP8-MXFP4 | 131072 | 10.50 | 4569.64 |
| Flash | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 1048576 | 8.04 | 124.36 |
| Flash | 64 | 16 | 3 | Hybrid MXFP8-MXFP4 | 1048576 | 9.46 | 422.88 |
| Flash | 16 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 6.27 | 159.49 |
| Flash | 256 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 8.41 | 1902.50 |
| Flash | 1536 | 16 | 1 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 15.95 | 6017.70 |
| Flash | 16 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 131072 | 6.45 | 155.03 |
| Flash | 256 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 131072 | 9.22 | 1735.36 |
| Flash | 16 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 1048576 | 7.71 | 129.70 |
| Flash | 64 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 1048576 | 9.11 | 439.08 |
| Flash | 256 | 16 | 3 | Hybrid FP8-MXFP4 | 8192 | 11.06 | 1447.00 |
| Flash | 1536 | 16 | 1 | Hybrid FP8-MXFP4 | 8192 | 24.28 | 3953.49 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 17.64 | 56.7 |
| Pro | 64 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 19.03 | 210.16 |
| Pro | 128 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 20.61 | 388.23 |
| Pro | 3072 | 64 | 1 | Hybrid MXFP8-MXFP4 | 8192 | 27.79 | 1727.24 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 19.46 | 51.38 |
| Pro | 64 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 21.23 | 188.42 |
| Pro | 16 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 16.33 | 61.24 |
| Pro | 64 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 17.23 | 232.22 |
| Pro | 128 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 8192 | 18.68 | 428.16 |
| Pro | 16 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 131072 | 16.55 | 60.44 |
| Pro | 64 | 16 | 3 | Hybrid HiF8-MXFP8-MXFP4 | 131072 | 18.22 | 219.57 |

来源称 MTP3 平均每 3 个 Draft Token 接受 1.44 个，MTP1 平均每 1 个接受 0.7 个；未给完整输入与统计过程，不能用于保证新任务的接受率或自行折算收益。

## Limitations 与验证

混合格式由多个模块共同构成，因此本卡不写量化 OR Scope；GBS、Chips、Seq Length、MTP 和规格也不能跨行拼接。按[部署验收流程](../../guides/models/deepseek_v4_deployment.md)保留实际输入、输出、接受率与计时记录，关闭性能上界设置后另验精度。来源自报不等于本仓复现。

## Evidence

- [deepseek_v4_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md)（primary）
