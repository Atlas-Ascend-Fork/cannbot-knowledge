---
type: API
title: MetricsProfStop
description: 设置性能数据采集信号停止，与MetricsProfStart配合使用，用于指定msOpProf调优的kernel侧代码段范围。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/performance_stats/MetricsProfStop.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# MetricsProfStop

设置性能数据采集信号停止，与MetricsProfStart配合使用，用于指定msOpProf调优的kernel侧代码段范围。

SIMD场景下，设置性能数据采集信号停止，和asc_prof_start配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段范围。

本接口组包含 asc_prof_stop, MetricsProfStart。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [性能调优（调试与调优）](../../../../../guides/programming_guide/debug_and_tuning/performance_tuning.md)（`explains`）：焦点处理MetricsProfStop 标定性能采集区间；性能调优（调试与调优）正文界定“通过毕昇编译器编译生成可执行程序后，使用msOpProf工具采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [MetricsProfStart](metrics_prof_start.md)（`same_topic`）：焦点处理MetricsProfStop 标定性能采集区间；MetricsProfStart正文界定“设置性能数据采集信号启动，与MetricsProfStop配合使用，用于指定msOpProf调优的kernel侧代码段范围”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [asc_prof_start](../../../../utils_api/tuning_interface/asc_prof_start.md)（`same_topic`）：焦点处理MetricsProfStop 标定性能采集区间；asc_prof_start正文界定“SIMD场景下，用于设置性能数据采集信号启动，和asc_prof_stop配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [asc_prof_stop](../../../../utils_api/tuning_interface/asc_prof_stop.md)（`same_topic`）：焦点处理MetricsProfStop 标定性能采集区间；asc_prof_stop正文界定“SIMD场景下，设置性能数据采集信号停止，和asc_prof_start配合使用。使用msOpProf工具进行算子上板调优时，可在kernel侧代码段前后分别调用asc_prof_start和asc_prof_stop来指定需要调优的代码段”。候选是采集区间的 Start/Stop 对或 msOpProf 调优流程，直接决定采集窗口。
- [性能统计](performance_stats.md)（`same_topic`）：MetricsProfStop 关闭由 MetricsProfStart 开启的采样，缺少它会失去明确的测量区间。
<!-- cannbot:related:end -->
