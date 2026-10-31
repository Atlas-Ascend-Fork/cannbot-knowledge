---
type: Runbook
title: MTP/DSpark 开启 Profiling 后 Decode 平均时延失真或显示零
description: 在 MTP/DSpark 的统计分支中检查计时窗口、接受长度与实际输出数是否对齐，使用 post-profile 统计并在空窗口时回退完整 Decode 数据。
tags:
- task.debugging
- topic.performance.analysis
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/infer.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/forward_data_info/forward_data_info.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/1193
  role: evidence
created_at: '2026-10-29T04:09:04Z'
updated_at: '2026-10-29T15:24:40Z'
platforms:
- agnostic
---

# MTP/DSpark 开启 Profiling 后 Decode 平均时延失真或显示零

## 适用范围

本配方针对固定 `log_results` 中 `next_n > 0` 的 MTP/DSpark 统计分支。普通非投机 Decode 的 `next_n = 0` 分支仍需单独核对 `process_infer_time`，不能假定它也使用 timed 窗口。

## 症状与快速检查

同一模型打开 Profiling 后平均 Decode 或投机等效时延明显失真，短请求可能打印 0.00 ms。先区分日志中的完整 Decode 接受率与排除采集窗口后的平均耗时，核对请求是否在采集结束前就完成。

## 诊断与根因

旧路径没有把 post-profile 的耗时与对应的验证轮次、接受数独立保存。使用一个窗口的耗时除以另一个窗口的接受长度会产生错误折算；空窗口不能当作零成本。

PR1193 增加 timed_infer_time、timed_spec_num_forward_ct、timed_spec_num_accepted_tokens 和 timed_decode_output_tokens。固定版本的 Decode 采集设置是 skip_first=3、active=3；正常从 Prefill 进入 Decode 后，完成这 6 步再开始计时。不启用 Profiling 时从真实 Decode 开始统计。Decode-only 的 profiler 初始化存在单独分支，不能直接套用该窗口假设。

## 修复与验证

采用修复后的 ProfilerManager、Executor 状态收集与 offline log_results 整套实现。等效时延用 post-profile 平均每轮耗时除以同窗口平均接受长度；完整过程的接受率和接受长度仍独立上报。无 post-profile 验证样本时，回退完整 Decode 数据，并使用完整接受长度。

覆盖关闭/开启 Profiling、短于/长于采集窗口的请求、MTP/DSpark、提前终止及静态 batch 尾部。逐项核对计时轮次、耗时总和、接受数和真实输出 token。每 delivered token 的模型执行时延日志排除调度成本，不能直接充当服务端到端 TPOT。

## 回退与残留风险

需回退代码时同时回退采集与汇总，保留原始计时数据和窗口标记。不能只关闭零除保护来消除 0.00 ms，也不能混用新旧字段。通用度量定义见 [投机解码双口径规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)。

## Evidence

- [infer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/infer.py)（primary）
- [profiler_context.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py)（supporting）
- [forward_data_info.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/forward_data_info/forward_data_info.py)（supporting）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/1193)（evidence）
