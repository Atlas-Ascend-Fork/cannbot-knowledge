---
type: Optimization
title: DeepSeek-V4 A3 Pod整数量化的来源性能观测
description: 保留 V4 Flash在A3 Pod的两行Offline Decode自报数据及W8A8C16、MTP1与强制EPLB条件。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: primary
created_at: '2026-10-21T09:02:45Z'
updated_at: '2026-10-29T15:09:57Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      serving_mode:
      - offline
---


# DeepSeek-V4 A3 Pod整数量化的来源性能观测

## Workload

来源固定指南的 DeepSeek-V4 Flash Offline Decode，不含 Serving 调度或框架负载均衡。序列字段为 8192，GBS 分别为 7168、8192；输入/输出拆分与请求并发未完整给出。

## Hardware

Atlas A3 Pod，64 Chips，Attention DP 与 MoE EP；不与 950DT 的浮点混合格式行直接比较，也不补造 die/进程数。

## Software

来源固定到上述提交，但没有为这些数字给出完整的实际软件 build、测量脚本和运行日志。安装章节中的示例环境不自动等于 benchmark 环境。

## Metric Definition

TPOT 与 Throughput 沿用源表字段和单位；来源未完整说明计时起止、分母、是否含首 token，以及全部预热/统计处理。不要从标签自行补充计算公式或作为服务端到端指标。

## Repetition and Variance

来源未给 warmup、重复次数、方差/置信区间，也未公开可绑定每行数据的运行记录。本仓没有独立复测，不创建 verified。

## Baseline 与 Variant

两行均为 W8A8C16、MTP1 与强制 EPLB，LI Cache 为 INT8、KV Cache 为 BF16；区别是 GBS。没有禁用量化、MTP 或强制 EPLB 的匹配基线，不能用本表单独证明某项优化的净收益。模块精度见[整数量化机制](../../concepts/quantization/int8_int4_hybrid.md)。

## Result

| 平台 | 规格 | Chips | GBS | MTP | DataType | Seq Length | TPOT(ms) | Throughput(Tokens/p/s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A3 Pod | Flash | 64 | 7168 | 1 | W8A8C16 | 8192 | 27.82 | 4025 |
| A3 Pod | Flash | 64 | 8192 | 1 | W8A8C16 | 8192 | 29.17 | 4388 |

来源报告 MTP1 平均每 1 个 Draft Token 接受 0.7 个；输入分布和统计过程未给出，不外推到新的任务。

## Limitations 与验证

GBS 变化不能直接映射为并发，也不把每行条件拆到其他平台或量化方案。参照[部署验收流程](../../guides/models/deepseek_v4_deployment.md)记录完整软硬件、配置、输入输出、重复与波动；本次没有独立复测，不给精度或性能保证。

## Evidence

- [deepseek_v4_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md)（primary）
