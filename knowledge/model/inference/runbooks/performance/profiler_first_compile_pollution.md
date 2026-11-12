---
type: Runbook
title: Profiling 首次编译污染：分开 Decode 预热与稳态采样
description: 首次 Decode 编译耗时混入性能采样、首步异常慢或 step_trace_time 首行 Computing 突增时，在采集窗外预热目标 torch.compile/JIT 路径，区分冷启动与稳态结果。
tags:
- task.debugging
- topic.performance.analysis
- topic.graph_execution
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
created_at: '2026-11-09T09:23:49Z'
updated_at: '2026-11-10T03:19:32Z'
platforms:
- a2
- a3
aliases:
- Profiling 首步异常慢
- Decode 编译污染
- Profiler 预热
---

# Profiling 首次编译污染：分开 Decode 预热与稳态采样

## 症状与探针

第一个 Decode step 远慢于后续，step_trace_time.csv 首行 Computing 异常大，trace 前段集中在图构建、绑定和下发，实际 kernel 稀疏。记录第一次触发 torch.compile/TorchAir/JIT 的调用发生在 Prefill 还是 Decode，核对目标 batch、q_len 与后端是否已预热。

## 根因与修复

移出窗口的应是首次触发目标路径编译/trace 的调用，不能一概认为是 Prefill 太慢。固定 Executor 的 Prefill 走 eager，Decode 才触发图模式；只预热 Prefill 仍可能把首次 Decode 编译采进去。

在采集窗口外用目标配置完成相应 Prefill、Decode 以及必要的宽度/shape 预热，并按目标异步运行方式确认完成，然后启动 profiler。要分析 Prefill 时仍采真实 Prefill kernel，只剔除事先定义的非目标编译阶段；要测冷启动时反而应保留编译成本并单独报告。

## 验证、回退与边界

对比预热后的多个 step，检查是否还有重编译或新 shape 特化。来源“首行大10倍”只是排查线索，没有通用阈值。用关闭 profiler 的稳态基线复核时延，不能拿带采集开销的 kernel 时间冒充 TPOT。新 shape 仍编译时回到签名定位，不通过跳过更多步骤隐藏异常；保留冷启动和稳态两份明确窗口。

相关：[Decode 编译入口](../../guides/optimization/graph_mode_decode_only_compile_backends.md)、[重复编译](graph_mode_stable_input_signature_recompile.md)。

## Evidence

- [.agents/skills/model-infer-profiling/references/troubleshooting.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md)
- [executor/utils/graph_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/graph_utils.py)
- [executor/core/model_worker/model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)
