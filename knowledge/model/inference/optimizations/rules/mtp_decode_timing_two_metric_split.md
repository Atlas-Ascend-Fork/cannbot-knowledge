---
type: Optimization
title: MTP / 投机解码 decode 计时：拆「每 step 时延」与「每等效 token 时延」两口径分报
description: 评估 DSA 稀疏注意力的 MTP 推测解码收益时，区分 LI/SFA 等模块的访存与计算变化，再以统一度量口径分报 Decode 每 step 时延、每等效 token 时延及实际交付 token 耗时；计时窗口和接受长度必须对应。
tags:
- task.optimization
- topic.speculative_decoding
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/infer.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/offline_inference.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/server.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T16:10:39Z'
platforms:
- agnostic
---

# 投机解码：每轮、等效 token 与实际交付 token 分开计时

## 同一窗口内计算

当前 `offline/infer.py::log_results` 同时服务 MTP、DSpark。设匹配窗口中模型执行耗时总和为 T、请求验证轮数为 N、接受 draft 总数为 A：

| 指标 | 口径 |
| --- | --- |
| 每轮时延 | T/N |
| 平均接受长度 | A/N + 1 |
| 等效 token 时延 | (T/N)/(A/N+1) |
| 实际交付 token 执行耗时 | T/该窗口实际交付 token 数 |

最后一项会受到 EOS/最大长度截断影响，与接受前缀分母不同；这里只统计模型执行，包含主模型及各次 draft，不含服务排队、调度和网络。

## 当前字段与回退

完整接受率使用 `sum(spec_num_accepted_tokens)/sum(spec_num_draft_tokens)`；只有没有实际 draft 字段时才回退 N×next_n，动态提案不能总用固定宽度估算。零草稿返回 0 接受率，零前向返回接受长度 1。

Profiler 结束后计时使用 `decode_execution_time`、`timed_spec_num_forward_ct` 与 `timed_spec_num_accepted_tokens`；分母须同窗口。若 timed 轮数为 0，回退 `full_decode_execution_time` 和完整接受长度；再缺才取普通 Decode 时间列表均值。完整接受率/长度仍单独报告，不能代替 timed 分母。

`OfflineInference` 按请求完成前的验证轮数截取完整执行时间，排除静态 batch 中请求完成后附带执行；EOS/最大长度截断后的 Decode 输出数另存 `decode_output_tokens/timed_decode_output_tokens`。多模态入口先排除 Encode 和 Prefill（列表前两项），普通文本排除首项 Prefill。

## 日志和验收

引擎返回 main 与 draft 各步耗时，总时延为二者相加；调度日志 MTP 按步标记，DSpark 汇总提案耗时。在线服务另报告请求级及累计接受统计，不能当成 offline 执行时间或端到端时延。

对照实验须保存输入、batch、宽度、采样、窗口、接受数、实际交付数与重复测量。只报一个“average inference time”不足以区分单轮开销和提案收益。定位窗口错配见[Profiling 后平均时延失真](../../runbooks/performance/post_profile_decode_latency.md)。

## Evidence

- [infer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/infer.py)（primary）
- [offline_inference.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/offline/offline_inference.py)（implementation）
- [execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)（implementation）
- [scheduler.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/scheduler/scheduler.py)（implementation）
- [server.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/server.py)（implementation）
