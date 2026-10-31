---
type: Optimization
title: Kimi K3 950DT：固定接受长度折算的 Decode 时延观测
description: 记录 32 卡、100K 输入、256 输出与接受长度按 4 折算下的约 28→10 ms 观测，保留仅统计主草稿模型耗时的边界。
tags:
- task.testing
- topic.performance.analysis
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k3/kimi_k3_inference_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/995
  role: evidence
created_at: '2026-10-29T04:09:03Z'
updated_at: '2026-10-29T15:29:18Z'
platforms:
- '950'
---

# Kimi K3 950DT：固定接受长度折算的 Decode 时延观测

## Workload

Kimi K3 完整 93 层、896 routed experts；输入 100K token，输出 256 token，单卡 batch=1，7 个草稿 token。

## Hardware

来源报告昇腾 950DT 32 卡，KDA TP16；其余模块并行方式以同版本技术文档和实际配置为准。

## Software

固定 cann-recipes-infer 提交 来源工作项 及 PR995。该观测段未给出足以完整复现实验的软件包与驱动矩阵。

## Baseline 与 Variant

基线等效 Decode 时延约 28 ms；变体叠加部署策略、多流、通信后端、融合算子、量化、MegaKDA/ReplaySSM 和 SuperKernel，降至接近 10 ms。文档瀑布图标注终点 10.3 ms。这是累计方案，未提供每项独立受控消融。

## Metric Definition

只统计主模型与 DSpark 耗时，接受长度统一按 4 折算。该值不覆盖请求排队、完整服务调度和网络时间，也不是按每个请求实际接受率测得的服务 TPOT。

## Repetition and Variance

来源未给 warmup、独立重复次数、方差或置信区间。本批未独立复测。

## Result 与 Limitations

来源将累计结果概括为约 2.8 倍加速；不能外推到大 batch、高吞吐或其他接受长度，不能把近似终点、固定折算与真实端到端时延混用。

## Evidence

- [kimi_k3_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k3/kimi_k3_inference_guide.md)（primary）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/995)（evidence）
