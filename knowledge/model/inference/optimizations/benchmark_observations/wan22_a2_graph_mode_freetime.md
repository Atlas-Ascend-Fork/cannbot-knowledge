---
type: Optimization
title: Wan2.2 A2 图模式观测：低 freetime 下暂缓启用
description: 记录 Issue 33 对 Wan2.2-I2V/A2 的 720P、480P 单步 freetime 自报及暂不启图的判断；无图模式前后对比，不将百分比当收益保证或通用阈值。
tags:
- task.optimization
- topic.graph_execution
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/33
  role: evidence
created_at: '2026-10-20T12:16:14Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- a2
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      objective:
      - latency
      model_features:
        all_of:
        - dit
---

# Wan2.2 A2 图模式观测：低 freetime 下暂缓启用

## 规则入口

本页是[图模式决策](../rules/graph_mode_enable_decision_profiling.md)的特定观测，保存来源数据与缺口，不重新维护“是否入图”的通用判断。

## Workload 与 Hardware

来源为 cann-recipes-infer Issue 33：目标 Wan2.2-I2V，Atlas A2，多卡视频生成；报告分别讨论 720P 与 480P。未给出这两个观测点的确切卡数、帧数、batch、并发、序列长度或量化，不能从支持目标推算测量配置。

## Software、Baseline 与 Variant

来源未固定测量源码 revision、CANN/PTA 版本，也未提供启用图模式后的 Variant 或可复现脚本。这里保留 RFC/Issue 的原始观测，不把后续模型实现当成这些数字的测量环境。

## Metric Definition、Result 与 Repetition

Issue 作者报告单个 step 的 freetime 占比：720P 为 0.1%，480P 为 0.5%，据此判断收益低、暂不启用图模式。来源未完整定义计时区间、分母、warmup、重复次数和方差；没有端到端时延或图模式前后收益，不能将百分比直接当作加速上限或保证。

## Limitations 与验证

该观测只说明当时的判断，不证明 Wan 在所有负载下不应入图，也不推广到所有 DiT。需要复现时先补全硬件/软件、输入、计时与统计口径，再独立比较合法执行模式、端到端指标和输出验收；本次未执行实验。没有 `verified`，不声明 Prefill/Decode 或未核验的执行模式。
