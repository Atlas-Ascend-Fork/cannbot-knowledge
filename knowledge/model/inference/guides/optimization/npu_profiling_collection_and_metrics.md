---
type: Guide
title: NPU Profiling 采集：ProfilerManager 窗口、Level1 与指标配置
description: NPU Profiler 只生成基本计数或基础指标、缺流水利用率时，核对 Level1、PipeUtilization、record_shapes 和手动采集窗口；另列 CANN Executor
  的 ProfilerManager 配置。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py
  role: supporting
created_at: '2026-11-09T09:23:48Z'
updated_at: '2026-11-10T01:26:11Z'
platforms:
- a2
- a3
aliases:
- Profiler 基础指标
- Profiler 基本计数
- torch_npu.profiler 详细指标
---

# NPU Profiling 采集：ProfilerManager 窗口、Level1 与指标配置

## 适用范围与入口

适用于来源记录的 Atlas A2/A3 torch_npu.profiler 推理采集；SDK 字段和产物随版本变化，不外推到未声明平台。下节的配置表仅属于 CANN Executor：统一 Executor 用 model_config.enable_profiler 启用 ProfilerManager，代码入口是 executor/utils/profiler_context.py，不能按旧 ModelRunner 的另一套默认值推断当前离线路径。

## CANN Executor 的内置窗口

| 阶段 | 固定代码的配置 | 输出位置 |
| --- | --- | --- |
| Prefill | active=1、skip_first=0、warmup=0、repeat=1 | res/.../prof/prefill |
| Decode | active=3、skip_first=3、warmup=0、repeat=1 | res/.../prof/decode |
| MM Encode | 同 Prefill 的创建分支 | res/.../prof/mm_encode |

ProfilerManager 首次状态为 Decode 时不启动采集，且开始 Decode 后不再切换阶段；做 Decode-only 改造必须保留状态生命周期。YAML 只提供总开关，不能虚构 active/skip_first 字段。若手动注入，明确指定 phase、调用 step/回调并把首次编译移出目标采集窗口；单步 Prefill 不是天然无效数据。

ProfilerManager 的 set_status 接收 ProfilerPhase，check_if_update 决定是否切换；create_profiler 创建实例，on_trace_ready 由 torch_npu.profiler.tensorboard_trace_handler 导出。enable_profiler=False 时返回空上下文；不能把手动 prof.step() 循环和该管理器的阶段生命周期混成一套。

## 独立于 Executor 的手动注入入口

来源还提供无内置采集或内置产物不可用时的 `torch_npu.profiler` 注入路径。它依赖可访问的推理步骤、profiler API 和匹配的 NPU 软件环境，不依赖 `ProfilerManager`。在目标推理进程的采集窗口创建 profiler，传入所需 `_ExperimentalConfig`，将目标 Prefill/Decode 调用放入窗口并逐步调用 `prof.step()`，退出后验收导出文件。首次编译移到目标窗口之外，窗口收尾见[不完整采集](../../runbooks/performance/profiler_schedule_incomplete_trace.md)。

SGLang、vLLM 等框架可据此检索通用采集知识；具体注入点、worker/rank 生命周期及版本兼容性仍须核对各自实现，未在这里验证。上面的 `model_config.enable_profiler`、固定 active/skip_first 和 `res/.../prof/` 路径不能直接套用。因此本卡不以 framework 硬过滤；无对应框架证据时适用性保持 unknown。

## 指标选择

_ExperimentalConfig(profiler_level=ProfilerLevel.Level1, aic_metrics=AiCMetrics.PipeUtilization) 是固定框架的默认组合，便于分析 Cube/Vector/MTE 流水。Level0 偏基础时间线，Level2 与其他指标组按安装版本能力选择；aic_metrics 一次选择一组。来源另列 ArithmeticUtilization、Memory、MemoryL0、MemoryUB、ResourceConflictRatio 和 L2Cache，是否可用与具体含义以安装版本为准；Memory/L2Cache 与 PipeUtilization 的测量目的不同，不能由一组计数直接声称已测另一组带宽。

record_shapes 控制形状采集，with_stack 控制调用栈，profile_memory 控制内存采集；固定框架三者均为 False。Level1 不保证 Input Shapes 一定有值，也不保证固定47列；来源在特定环境见过9列与约47列，只是线索。改配置后核对所需列及其非空情况，再决定是否可用于当前分析。

## 产物、成本与验收

分阶段、rank 核对 kernel 明细和合法 trace JSON，查看 parser 日志；通信文件需实际采到通信，不要求单卡产生 communication.json。内存和调用栈采集会增加开销与数据体积，profiling 时间不替代无采集基线。TensorBoard 面板缺失可核对 torch_tb_profiler 插件，也可直接用兼容的 Chrome trace 查看器读取时间线。

相关：[产物目录识别](npu_profiling_artifact_layouts.md)、[字段解释](kernel_details_field_interpretation.md)、[窗口收尾](../../runbooks/performance/profiler_schedule_incomplete_trace.md)、[CSV 解析失败](../../runbooks/performance/profiler_csv_parse_failure.md)、[编译污染](../../runbooks/performance/profiler_first_compile_pollution.md)。

## Evidence

- [.agents/skills/model-infer-profiling/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md)
- [.agents/skills/model-infer-profiling/references/troubleshooting.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md)
- [executor/utils/profiler_context.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/profiler_context.py)
- [executor/core/engine/execution_engine.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/engine/execution_engine.py)
