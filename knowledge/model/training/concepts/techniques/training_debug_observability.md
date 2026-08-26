---
type: Concept
title: torchtitan-npu 训练调试可观测性（Flight Recorder / Memory Snapshot / Profiling）
description: torchtitan-npu 训练调试可观测：(1)HCCL Flight Recorder——tools/flight_recorder.py 拦截 init_distributed 自动设 TORCH_HCCL_TRACE_BUFFER_SIZE 等 HCCL env（trace_buf_size>0 启用），超时阈值用 HCCL_EXEC_TIMEOUT，超时 dump comm_traces/rank_*；CommConfig。(2)Memory Snapshot——ProfilingConfig.enable_memory_snapshot 定期+OOM 自动 dump .pickle，PyTorch memory_viz 看。(3)Profiling——torch_npu.profiler，原生 freq 模式(profile_freq) vs npu 扩展步数模式(profile_step_start/end/profile_ranks/profile_record_shapes/enable_online_parse)。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/metrics_and_debugging.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torchtitan-npu 训练调试可观测性

## Summary

torchtitan-npu 为昇腾分布式训练提供三类调试可观测性特性，分别针对通信故障、内存问题和性能瓶颈。三者配置都写在各模型的 `config_registry.py` 配置函数中（`CommConfig` 或 `ProfilingConfig`），可由命令行参数覆盖。

| 使用场景 | 对应功能 | 配置类 |
|---------|---------|-------|
| 排查 HCCL 通信超时 | [HCCL Flight Recorder](#hccl-flight-recorder) | `CommConfig` |
| 分析 OOM / 内存泄漏 | [Memory Snapshot](#memory-snapshot) | `ProfilingConfig`（原生） |
| 定位性能瓶颈 | [Profiling](#profiling) | `ProfilingConfig`（原生 + NPU 扩展） |

---

## HCCL Flight Recorder

大规模分布式训练因通信算子超时而异常退出时，常因缺少通信轨迹及代码位置信息难以定位根因。Flight Recorder 自动配置 HCCL 环境变量，实时记录通信算子的下发调用栈、时间戳和数据量大小；检测到超时时自动把缓冲区轨迹转储到文件。

### 实现原理

启用所需的环境变量与 NCCL 存在差异，因此 torchtitan-npu 在 [`torchtitan_npu/tools/flight_recorder.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/tools/flight_recorder.py) 中用 `init_distributed_with_hccl_flight_recorder` 拦截 `torchtitan.distributed.utils.init_distributed`（`distributed_utils.init_distributed = init_distributed_with_hccl_flight_recorder`），在分布式初始化阶段按配置自动 `_warn_overwrite_env` 设置以下环境变量：

1. **`TORCH_HCCL_TRACE_BUFFER_SIZE`** — 追踪缓冲区大小，控制记录的通信轨迹数据量（始终设置为 `trace_buf_size`）。
2. **`HCCL_ASYNC_ERROR_HANDLING`** — 启用异步错误处理，创建检测通信问题的 HCCL Watchdog 线程。
3. **`TORCH_HCCL_ENABLE_MONITORING`** — 启用 HCCL 监控，实时检测通信状态。
4. **`TORCH_HCCL_DUMP_ON_TIMEOUT`** — 检测到超时时自动转储追踪信息。
5. **`TORCH_HCCL_DEBUG_INFO_TEMP_FILE`** — 追踪文件的存储路径和文件名前缀（`{dump_dir}/{prefix}`）。

> 关键点：仅 `TORCH_HCCL_TRACE_BUFFER_SIZE` 无条件设置；后 4 个环境变量及 dump 目录创建仅在 `if comm_config.trace_buf_size > 0:` 分支下启用。

### 配置选项（`CommConfig`）

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `trace_buf_size` | int | 0 | 追踪缓冲区大小。0 时不启用追踪；>0 时启用自动追踪和超时转储。 |
| `save_traces_folder` | str | `"comm_traces"` | 追踪文件保存目录，相对训练输出目录。 |
| `save_traces_file_prefix` | str | `"rank_"` | 追踪文件名前缀。 |

HCCL 通信超时阈值目前只能通过环境变量 `HCCL_EXEC_TIMEOUT` 配置（例如 `export HCCL_EXEC_TIMEOUT=120` 设为 120 秒），以确保 HCCL 其他调试信息能被正确收集。

```python
from torchtitan.config import CommConfig

comm = CommConfig(
    trace_buf_size=2000,
    save_traces_folder="hccl_traces",
    save_traces_file_prefix="rank_",
)
```

超时/错误时轨迹转储到 `hccl_traces/rank_*`，可按 PyTorch 社区 [Flight Recorder 教程](https://docs.pytorch.org/tutorials/unstable/flight_recorder_tutorial.html) 分析。

---

## Memory Snapshot

内存快照捕获训练过程中的内存分配、显存占用、张量生命周期等信息。这是 torchtitan **原生**功能（`ProfilingConfig`），生成 `.pickle` 格式快照，可用 PyTorch [memory_viz](https://docs.pytorch.org/memory_viz) 工具可视化。适用于 OOM 排查、内存泄漏追踪、显存优化分析。

### 配置选项（`ProfilingConfig` 原生）

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enable_memory_snapshot` | bool | false | 是否启用内存快照。 |
| `save_memory_snapshot_folder` | str | `"memory_snapshot"` | 快照保存目录。 |
| `profile_freq` | int | 10 | 每隔多少训练步收集一次快照。 |

机制：按 `profile_freq` 频率定期收集，并在发生 OOM 时**自动转储**当前快照到 `save_memory_snapshot_folder`。

```python
from torchtitan_npu.config.configs import ProfilingConfig

profiling = ProfilingConfig(
    enable_memory_snapshot=True,
    save_memory_snapshot_folder="memory_snapshot",
    profile_freq=10,
)
```

---

## Profiling

torchtitan-npu 对性能分析做了 NPU 适配，使用 `torch_npu.profiler` 原生分析器追踪 CPU 与 NPU 活动，记录内存、调用栈、张量形状，并提供 AI 算力利用率指标（`AiCMetrics.ArithmeticUtilization`、`ProfilerLevel.Level1`、`ProfilerActivity.CPU` + `ProfilerActivity.NPU`）。

### torchtitan 原生配置选项

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `enable_profiling` | bool | false | 是否启用性能分析。 |
| `save_traces_folder` | str | `"profile_traces"` | 分析结果保存目录。 |
| `profile_freq` | int | 10 | 采样频率，每隔多少步采集一次。 |
| `profiler_warmup` | int | 1 | 预热步数。 |
| `profiler_active` | int | 3 | 采集步数。 |

### torchtitan-npu 扩展配置选项

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `profile_step_start` | int | 0 | 开始分析的步数。>0 时启用**基于步数**的分析模式。 |
| `profile_step_end` | int | 0 | 结束分析的步数。必须 >0 才会激活基于步数模式（与 `profile_step_start > 0` 共同构成进入条件，见[两种模式](#两种模式)）。配置项 docstring 声称「为 0 时取 `profile_step_start + profiler_active`」，但该回退在当前代码路径中不可达：step_end==0 时根本不进入基于步数分支，直接落到基于频率的 `else`。 |
| `profile_ranks` | list[int] | `[-1]` | 需分析的 rank 列表（如 `[0, 1, 2]`）；`[-1]` 表示所有 rank。 |
| `profile_record_shapes` | bool | true | 是否记录张量形状。 |
| `profile_with_memory` | bool | false | 是否记录内存使用。 |
| `profile_with_stack` | bool | false | 是否记录调用栈。 |
| `enable_online_parse` | bool | true | 是否在线解析；为 False 时 `on_trace_ready=None` 且设 `ASCEND_WORK_PATH` 走离线解析。 |

### 两种模式

- **基于频率（原生）**：`enable_profiling=True` + `profile_freq` / `profiler_warmup` / `profiler_active`，周期性采集。
- **基于步数（NPU 扩展）**：`profile_step_start > 0` 且 `profile_step_end > 0` 时激活（`if profile_step_start > 0 and profile_step_end > 0:` 分支），按 `wait/warmup/active` 调度精确采集指定步区间的指定 rank。承重判据：`active = profile_step_end - profile_step_start`、`wait = profile_step_start - global_step - 2`、`warmup = 1 if profile_step_start > global_step + 1 else 0`。即 `profile_step_start` 必须大于「当前续训步 `global_step` + 2」，否则 `wait < 0` 会直接 `yield None` 跳过整段 profiling 并告警（`profile_step_start must be greater than {global_step} + 2`）——配置 step 区间时最易踩的关键约束。

```python
from torchtitan_npu.config.configs import ProfilingConfig

profiling = ProfilingConfig(
    enable_profiling=True,
    save_traces_folder="profile_traces",
    profile_step_start=5,
    profile_step_end=6,
    profile_ranks=[0],
    profile_record_shapes=True,
    profile_with_memory=False,
    profile_with_stack=False,
    enable_online_parse=True,
)
```

---

## Evidence

- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/metrics_and_debugging.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/metrics_and_debugging.md)（三类可观测性特性使用指南）
- Flight Recorder 实现（@8f128cd）：[`torchtitan_npu/tools/flight_recorder.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/tools/flight_recorder.py)（`init_distributed_with_hccl_flight_recorder` 拦截 `init_distributed`、`_warn_overwrite_env` 设置 HCCL 环境变量）
- Profiling 实现（@8f128cd）：[`torchtitan_npu/tools/profiling.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/tools/profiling.py)（`AiCMetrics.ArithmeticUtilization`、`ProfilerLevel.Level1`、`ProfilerActivity.CPU` + `ProfilerActivity.NPU`、基于步数采集分支）

## Links

- [torchtitan](../frameworks/torchtitan.md)（实现所在框架）
- [deepseek-v32-pretrain](../../guides/recipes/deepseek_v32_pretrain.md)（应用 recipe）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（应用 recipe）
- [ttp-high-availability](ttp_high_availability.md)（故障容错：TTP 在故障时落一致 checkpoint，与可观测诊断 dump 互补）
