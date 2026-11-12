---
type: Guide
title: Profiling 产物识别：torch_npu ascend_pt 与原生 msprof 目录
description: 找到 kernel_details/trace_view 或 op_summary/msprof 配对文件，核对采集 run、phase、rank 与 device，避免混合多卡数据。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-perf-breakdown/references/prof_layouts.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md
  role: supporting
created_at: '2026-11-09T09:23:48Z'
updated_at: '2026-11-10T01:26:11Z'
platforms:
- a2
- a3
---

# Profiling 产物识别：torch_npu ascend_pt 与原生 msprof 目录

## 两类布局

torch_npu.profiler 通常按进程生成 <hostname>_<pid>_<timestamp>_ascend_pt，其中 ASCEND_PROFILER_OUTPUT/kernel_details.csv 是设备 kernel 明细，trace_view.json 是 Chrome trace；operator_details.csv 是 PyTorch 层，不能当 kernel 一对一明细。FRAMEWORK 与 PROF_* 保存原始数据，profiler_metadata.json 提供元数据线索。

按采集配置和版本还可出现 op_statistic.csv（算子统计）、api_statistic.csv（host API）、step_trace_time.csv（step 计算/通信）、memory_record.csv、l2_cache.csv 及 *.db。数据库导出与文本导出是不同产物形式，缺少某个可选文件不等于全部采集失败。

原生 msprof 通常生成 PROF_<id>_<timestamp>_<hash>，含 host/data、device_<id>/data 和 mindstudio_profiler_output。后者常有 op_summary_*.csv 与 msprof_*.json，以及 task_time/op_statistic/api_statistic 等文件；旧布局也可能在 device_<id>/summary/op_summary.csv 与 device_<id>/timeline/msprof_*.json。以实际目录和文件字段为准，不要求这些名字在所有版本同时存在。

wrapper 可能给文件改名，所以先打开 CSV 表头与 JSON 结构，确认是设备 kernel 明细及同一时间域的时间线。统计汇总表不能替代每次调用记录，文件改名不能证明字段或时间单位相同。

多卡实际采到通信时，可出现 communication.json 和 communication_matrix.json；文件缺失要核对是否真有通信和相应解析，不要求单卡也生成通信矩阵。某些采集包装另存 inputs.json 用于关联输入/配置，它不是所有 profiler 版本的必备文件。torch_npu 的 tensorboard_trace_handler、原始 PROF 数据和分析导出目录应按实际采集入口配对。

## 多 rank、设备与阶段

ascend_pt 名称里的 pid 不是 rank。device_<id> 是设备标识，不必等于全局 rank；跨节点每个节点的 device id 可以重复。phase 也不由通用目录名保证，需结合框架 prof/prefill 或 prof/decode 父路径、采集配置、metadata 与日志核对。

存在多次采集或多设备时，列出实际的 run/host/pid/rank/device/phase 对应关系。已由日志唯一确认的身份直接采用，证据仍不唯一时保留未知并补齐来源，不能默认选第一个目录。每个分析单元配对同一次采集、同 rank/device、同阶段的 CSV 与 trace；不把多个时间基准直接相减或合并成单卡时延。

## 验证与边界

读取少量表头、阶段标志及采样窗口，验证对应 kernel 和 trace 事件的时间范围/单位。目录发现只证明找到了候选文件，不证明 profiler 采集完整、精度正确或 rank 已确认。复用数据时保留配置与来源路径，错配时重新选择文件而不是修饰文件名。

相关：[字段解释](kernel_details_field_interpretation.md)、[采集与验收](npu_profiling_collection_and_metrics.md)。

## Evidence

- [.agents/skills/model-infer-perf-breakdown/references/prof_layouts.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-perf-breakdown/references/prof_layouts.md)
- [.agents/skills/model-infer-profiling/references/troubleshooting.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/references/troubleshooting.md)

- [.agents/skills/model-infer-profiling/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-profiling/SKILL.md)（supporting）
