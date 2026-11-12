---
type: Runbook
title: Profiler 停在 RECORD：Incorrect schedule 与 trace JSON 截断
description: 手动采集未跨出 active 窗口时，核对 step 次数、回调和实际 JSON；保留 torch_npu 版本差异，不按文件末字符判定完整。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py
  role: supporting
created_at: '2026-11-09T09:23:49Z'
updated_at: '2026-11-09T09:23:49Z'
platforms:
- a2
- a3
---

# Profiler 停在 RECORD：Incorrect schedule 与 trace JSON 截断

## 症状与快速检查

出现 Incorrect schedule: Stop profiler while current state is RECORD，trace_view.json 无法解析，或回调/CSV 缺失。先记录 torch_npu/CANN 版本、wait/skip_first/warmup/active/repeat、实际 prof.step() 次数及 on_trace_ready 是否执行；确认循环是否因 EOS 或异常提前结束。

## 根因与修复

schedule 在 step 时推进，退出 with 时仍处于 active 窗口，某些版本会强制停止而没有完成预期解析。来源手动采集示例限定 wait=0、repeat=1，采用保守预算 step 次数至少 skip_first + warmup + active + 1，或循环后补一次 step 推进收尾；warmup=2、active=30 时示例预算33次。调整 active/skip_first 后同时核对实际生成步数，不能只增 max_new_tokens 而忽略提前 EOS。

这不是所有 profiler 版本和框架生命周期的统一下标公式；wait、repeat 或显式 start/stop 不同需检查实际状态和回调。框架单步 Prefill 由 ProfilerManager.stop 管理，与手动 Decode 循环不同，不能仅因 active=1 判定无效，也不盲目给每个业务 forward 加一次。

## 版本证据与验证

来源报告 torch_npu≤2.7.x 的该症状更容易伴随解析失败；2.8.0.post2 上有 warning 但仍产出合法 JSON 的观测。它没有给所有补丁版本的保证，不能由版本号直接决定产物可用。

使用 json.load 验证整个文件，兼容数组或含 traceEvents 的对象形式；以是否以 ] 结尾只能辅助观察。检查目标窗口、CSV 行数及所需列，确认最后的有效 step 没遗漏，也未把收尾动作当额外推理样本。

## 回退与残留风险

保留原始采集和日志，在小窗口重新验证回调；仍缺 CSV 时转解析故障诊断。合法 JSON 不证明 CSV、phase 或 rank 正确，缺失数据不能补写成性能测量。

相关：[CSV 解析故障](profiler_csv_parse_failure.md)、[采集窗口](../../guides/optimization/npu_profiling_collection_and_metrics.md)。

## Evidence

- [.agents/skills/model-infer-profiling/references/troubleshooting.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md)
- [executor/utils/profiler_context.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py)
