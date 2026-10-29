---
type: Optimization
title: DeepSeek-V4 950DT混合量化的来源性能观测
description: 集中 V4 总览与量化卡已引用的 950DT 数据，补齐 GBS，保留 MTP、强制 EPLB 和统计缺口。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-10-21T09:02:44Z'
updated_at: '2026-10-21T09:02:44Z'
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

固定指南自报的 Offline Decode，不含 Serving 调度和框架负载均衡。下表集中旧 V4 总览和混合量化卡已引用的行，补回原表 GBS；不加入未被这两张卡引用的新测量点。Flash/Pro 分开，Seq Length 不补作输入/输出拆分，并发未给出。

## Hardware

950DT，16 Chips，Attention DP 与 MoE EP；不是 950PR 测量，也不把 16 Chips 自动换算为 die 或进程数。

## Software

来源固定到上述提交，但没有为这些数字给出完整的实际软件 build、测量脚本和运行日志。安装章节中的示例环境不自动等于 benchmark 环境。

## Metric Definition

TPOT 与 Throughput 沿用源表字段和单位；来源未完整说明计时起止、分母、是否含首 token，以及全部预热/统计处理。不要从标签自行补充计算公式或作为服务端到端指标。

## Repetition and Variance

来源未给 warmup、重复次数、方差/置信区间，也未公开可绑定每行数据的运行记录。本仓没有独立复测，不创建 verified。

## Baseline 与 Variant

两种 Hybrid 格式的模块配置由[混合量化机制](../../concepts/quantization/hybrid_mxfp8_mxfp4.md)维护。这里只在同规格、GBS、序列和 MTP 下比较来源结果；来源未提供完整受控试验记录。MTP 和强制 EPLB 同时参与，不能把整网结果归因给单一量化或多流开关。

## Result

| 规格 | GBS | Chips | MTP | DataType | Seq Length | TPOT(ms) | Throughput(Tokens/p/s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Flash | 256 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 9.84 | 1625.31 |
| Flash | 1536 | 16 | 1 | Hybrid MXFP8-MXFP4 | 8192 | 20.33 | 4722.22 |
| Flash | 256 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 10.69 | 1496.36 |
| Flash | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 1048576 | 8.22 | 121.70 |
| Flash | 256 | 16 | 3 | Hybrid FP8-MXFP4 | 8192 | 11.06 | 1447.00 |
| Flash | 1536 | 16 | 1 | Hybrid FP8-MXFP4 | 8192 | 24.28 | 3953.49 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 8192 | 17.64 | 56.7 |
| Pro | 16 | 16 | 3 | Hybrid MXFP8-MXFP4 | 131072 | 19.46 | 51.38 |

来源称 MTP3 平均每 3 个 Draft Token 接受 1.44 个，MTP1 平均每 1 个接受 0.7 个；未给完整输入与统计过程，不能用于保证新任务的接受率或自行折算收益。

## Limitations 与验证

混合格式由多个模块共同构成，因此本卡不写量化 OR Scope；GBS、Chips、Seq Length、MTP 和规格也不能跨行拼接。按[部署验收流程](../../guides/models/deepseek_v4_deployment.md)保留实际输入、输出、接受率与计时记录，关闭性能上界设置后另验精度。来源自报不等于本仓复现。

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_inference_guide.md)

本次核对固定来源及必要配置，不将文档自报、来源固定或 Lint 通过记作硬件验证事件。
