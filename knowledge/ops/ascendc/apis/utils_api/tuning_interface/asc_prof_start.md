---
type: API
title: asc_prof_start
description: SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/asc_prof_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# asc_prof_start

SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。

函数原型：__aicore__ inline void asc_prof_start()

返回值：无

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。

<!-- cannbot:related:start -->
## 相关

- [asc_mark_stamp](asc_mark_stamp.md)（`related`）：asc_prof_start/stop 定义指标采集窗口，mark_stamp 在窗口内细分执行路径。
- [性能统计](../../simd_api/basic_api/debug_interface/performance_stats/performance_stats.md)（`related`）：性能统计说明性能统计接口集，包含 MetricsProfStart、MetricsProfStop 等性能指标采集接口。
- [MetricsProfStart](../../simd_api/basic_api/debug_interface/performance_stats/metrics_prof_start.md)（`same_topic`）：MetricsProfStart 与 asc_prof_start 都向 profiling 流程发送开始采集信号，分别是基础 API 与 C 接口的直接对应入口。
- [MetricsProfStop](../../simd_api/basic_api/debug_interface/performance_stats/metrics_prof_stop.md)（`same_topic`）：焦点处理MetricsProfStop 标定性能采集区间；asc_prof_start正文界定“SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [asc_prof_stop](asc_prof_stop.md)（`same_topic`）：asc_prof_stop：asc_prof_start/stop必须包围同一采集区间；MetricsProfStart/Stop是另一套成对性能区间接口，可直接辅助避免起止混配。 目标卡《asc_prof_start》补充：SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。
<!-- cannbot:related:end -->
