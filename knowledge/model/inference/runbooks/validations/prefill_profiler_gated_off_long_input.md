---
type: Runbook
title: 配了 enable_profiler 却拿不到 prefill profile：长输入超 moe_chunk_max_len 时被静默门控关闭
description: 配了 enable_profiler 却拿不到 prefill profile：长输入超 moe_chunk_max_len 时被静默门控关闭。配置了 enable_profiler=True，却在 RES_PATH/prof/prefill 下拿不到 prefill 段 profile——而 prof/decode 正常有。不报错、不告警，profiling 静默缺失。
tags:
- task.debugging
- topic.long_context
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/301
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 配了 enable_profiler 却拿不到 prefill profile：长输入超 moe_chunk_max_len 时被静默门控关闭

## 信号（现象）

配置了 `enable_profiler=True`，却在 `RES_PATH/prof/prefill` 下拿不到 prefill 段 profile——而 `prof/decode` 正常有。不报错、不告警，profiling 静默缺失。

## 触发条件

DeepSeek-R1 / LongCat-Flash 两个 runner，且 `data_config.input_max_len` 配置值 **大于** `model_config.moe_chunk_max_len`（默认 `moe_chunk_max_len=65536`、`input_max_len=2048`）。默认配置（`input_max_len=2048 <= 65536`）下 prefill profiling 是开着的；只有把 `input_max_len` 配到超阈值（长序列场景）才触发静默关闭。

## 根因

这两个 runner 的 `__init__` 把 `enable_prefill_profiler` 用长度条件收紧——`input_max_len > moe_chunk_max_len` 时该开关为 `False`，prefill 段 `define_profiler(enable_profiler=False, ...)` 退化为 `FakeContextManager`、不落盘：

```python
self.moe_chunk_max_len = runner_settings["model_config"].get("moe_chunk_max_len", 65536)
self.input_max_len = runner_settings["data_config"].get("input_max_len", 2048)
self.enable_prefill_profiler = self.enable_profiler and (self.input_max_len <= self.moe_chunk_max_len)
```

`enable_decode_profiler` 仍沿用基类的 `= self.enable_profiler`，故 **decode 段不受此长度门控**——这解释了「decode 有 profile、prefill 没有」的非对称现象。基础 `ModelRunner` 及其它未覆盖该开关的模型不带此门控（其 `enable_prefill_profiler` 恒等于 `enable_profiler`）。

`moe_chunk_max_len` 是长序列 prefill 的 MoE 分块阈值（分块串行以压峰值显存，见 [moe-prefill-oom-peak-memory](../performance/moe_prefill_oom_peak_memory.md)）；门控与它挂钩暗示与长输入 MoE 分块采集开销 / 落盘体积相关，但源未给出选此阈值的明确理由（设计意图为推断，不作事实断言）。

## 修法

要在 DeepSeek-R1 / LongCat-Flash 上拿到 prefill profile，确保 `input_max_len <= moe_chunk_max_len`：调大 `model_config.moe_chunk_max_len`（默认阈值 65536）或减小 `data_config.input_max_len`。这属该门控的预期行为、非运行时报错——遇到「配了 profiler 但 prefill 无产出」先核这两个 [config](../../concepts/techniques/inference_config.md) 值的相对大小，而不是先怀疑 profiler 坏了。

同类「input_max_len 引起的长序列静默异常」还有 LongBench 下负索引尾切静默裁掉正文，见 [longbench-input-max-len-sysprompt](../validations/longbench_input_max_len_sysprompt.md)。

## Evidence

- `diff 事实`（@6a8f3c1683241161）：`runner_deepseek.py` 与 `runner_longcat_flash.py` 的 `__init__` 中 `moe_chunk_max_len`（默认 65536）、`input_max_len`（默认 2048）、`enable_prefill_profiler = enable_profiler and (input_max_len <= moe_chunk_max_len)` 三行逐字对上；两个 runner 均未覆盖 `enable_decode_profiler`，故 decode 不受门控亦为 diff 事实。仅这两个 runner 设此门控（按证据定范围，不外推其它模型）。
- `推断`（隔离，不并入事实面）：门控与 MoE 分块挂钩暗示与长输入采集开销 / 落盘体积相关，但 diff / 描述 / 讨论均未给选此阈值的理由。
- 溯源下探：[cann-recipes-infer-pr-301-feat-prefill-profiling](https://gitcode.com/cann/cann-recipes-infer/merge_requests/301)

<!-- cannbot:related:start -->
## 相关

- [MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置](../performance/moe_prefill_oom_peak_memory.md)（`related`）：- 引入 `moe_chunk_max_len`：当 `num_tokens > moe_chunk_max_len` 时按 `ceil(num_tokens/moe_chunk_max_len)` 沿 token 维把 `hidden_states / topk_ids / topk_weight` 均分，逐块串行做 expert dispatch/combine，使每块 `expanded_x` / `gathered_tokens` 稳定在 `~ moe_chunk_max_len × top_k × hidden`。；`moe_chunk_max_len` 是长序列 prefill 的 MoE 分块阈值（分块串行以压峰值显存，见 ［moe-prefill-oom-peak-memory］(../performance/moe_prefill_oom_peak_memory.md)）；门控与它挂钩暗示与长输入 MoE 分块采集开销 / 落盘体积相关，但源未给出选此阈值的明确理由（设计意图为推断，不作事实断言）。；焦点的长序列分块处置与 profiler 的同一阈值门控直接相连，可避免把缺失 profile 误判为采集器故障。
<!-- cannbot:related:end -->
