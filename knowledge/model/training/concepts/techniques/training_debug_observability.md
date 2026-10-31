---
type: Concept
title: 训练调试可观测性（内存快照与 NPU 性能分析）
description: 当前 profiler 分层参数、独立内存快照周期、可恢复绝对步数窗口及多 rank 离线解析；撤下已移除的 Flight Recorder 入口。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/metrics_and_debugging.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/tools/profiler.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- agnostic
---

# 训练内存快照与性能分析

## Summary

当前 torchtitan-npu 提供内存快照和 NPU Profiler。公共配置使用 `profiler.*`，NPU 选项位于 `profiler.extension.*`。旧版 Flight Recorder 自动注入 HCCL 环境变量的文件和拦截入口已移除，本页不再把该旧入口列为当前功能。

## 内存快照

`--profiler.enable-memory-snapshot` 启用周期快照，并在 OOM 时转储；默认目录 `profiling/memory_snapshot`，生成 pickle 供 memory_viz 分析。

`memory-snapshot-freq` 默认为 None，显式设置必须为正数；未设置时回退 `profile-freq`（默认 10）。绝对 profiling 窗口会推导新的 profile_freq，想保持快照独立周期时应显式指定 memory-snapshot-freq。

## 周期性能分析

`--profiler.enable-profiling` 开启采样，默认目录 `profiling/traces`。默认 profile_freq=10、profiler_warmup=3、profiler_active=1、profiler_repeat=None、profiler_skip_first=0。周期必须容纳 warmup+active，否则 wait 为负而报错。

NPU extension 的 profile_ranks 默认 [-1]（全 rank），也可限制为 0 等 rank 列表；profile_with_memory 和 profile_with_stack 默认 False，enable_online_parse 默认 True。当前实现固定记录 shapes，不再提供旧 profile_record_shapes 参数。采样活动包括 CPU/NPU、Level1 与 ArithmeticUtilization。

## 绝对步数与断点恢复

```bash
NGPU=2 bash scripts/run_train.sh \
  --profiler.enable-profiling \
  --profiler.extension.profiler-start 5 \
  --profiler.extension.profiler-end 6 \
  --profiler.extension.profile-ranks 0 \
  --profiler.extension.profile-with-memory
```

profiler_start/end 默认 None，必须成对设置、为正整数且 end>start；采样窗口为 [start,end)。布尔 CLI 是开关，后面不追加 true。

窗口推导 skip_first=max(start-warmup-1,0)，实际 warmup=start-1-skip_first，active=end-start，repeat=1。start 可以为 1，旧版要求至少 global_step+2 的限制已移除。恢复训练时首个 schedule 查询按恢复后的 global_step 对齐；已结束窗口不重复采样。profile_ranks 排除的进程不创建 profiler。

## 离线解析与验证

`--profiler.extension.no-enable-online-parse` 关闭在线解析，先转储原始数据。训练后运行：

```bash
python3 scripts/parse_profiling_data.py path/to/save_traces_folder
```

输入可为单个 `*_ascend_pt` 或父目录，脚本查找直接子目录及 `profiling_data/*_ascend_pt`，支持多 rank。每个采样目录的 ASCEND_PROFILER_OUTPUT 中产生 kernel_details.csv、api_statistic.csv、profiler DB 与 trace_view.json。

验证应核对所选 rank、绝对步数和恢复后窗口是否匹配，再分析稳态 kernel。开启 shape/stack/memory 记录有额外成本，勿将调试配置吞吐直接作为基线。本页基于源文档与实现静态复核，未执行 NPU 采样。

## Evidence

- [metrics_and_debugging.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/metrics_and_debugging.md)（primary）
- [profiler.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/extensions/torchtitan/tools/profiler.py)（implementation）

## Links

- [训练框架](../frameworks/torchtitan.md)
- [训练 AutoFuse](autofuse_train.md)
