---
type: API
title: MetricsProfStart
description: 设置性能数据采集信号启动，与MetricsProfStop配合使用，用于指定msOpProf调优的kernel侧代码段范围。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/performance_stats/MetricsProfStart.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# MetricsProfStart

设置性能数据采集信号启动，与MetricsProfStop配合使用，用于指定msOpProf调优的kernel侧代码段范围。

SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。

本接口组包含 asc_prof_start, MetricsProfStop。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [性能调优（调试与调优）](../../../../../guides/programming_guide/debug_and_tuning/performance_tuning.md)（`explains`）：性能调优指南给出 msOpProf 上板与 simulator 的采集分析流程，说明在什么调优任务中用 MetricsProfStart/Stop 限定 Kernel 代码段。
- [MetricsProfStop](metrics_prof_stop.md)（`same_topic`）：焦点处理MetricsProfStop 标定性能采集区间；MetricsProfStart正文界定“设置性能数据采集信号启动，与MetricsProfStop配合使用，用于指定msOpProf调优的kernel侧代码段范围”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [asc_prof_start](../../../../utils_api/tuning_interface/asc_prof_start.md)（`same_topic`）：MetricsProfStart 与 asc_prof_start 都向 profiling 流程发送开始采集信号，分别是基础 API 与 C 接口的直接对应入口。
- [asc_prof_stop](../../../../utils_api/tuning_interface/asc_prof_stop.md)（`same_topic`）：asc_prof_stop：asc_prof_start/stop必须包围同一采集区间；MetricsProfStart/Stop是另一套成对性能区间接口，可直接辅助避免起止混配。 目标卡《MetricsProfStart》补充：设置性能数据采集信号启动，与MetricsProfStop配合使用，用于指定msOpProf调优的kernel侧代码段范围。
- [性能统计](performance_stats.md)（`same_topic`）：性能统计入口页说明 MetricsProfStart/Stop 的配对方式，并指出新代码优先使用 asc_prof_start/stop。
<!-- cannbot:related:end -->
