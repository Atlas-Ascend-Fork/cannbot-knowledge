---
type: API
title: 性能统计
description: 性能统计接口集，包含 MetricsProfStart、MetricsProfStop 等性能指标采集接口。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/performance_stats/performance_stats.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 性能统计

提供 MetricsProfStart 和 MetricsProfStop 接口，用于设置性能数据采集信号的启动和停止，配合使用可在 kernel 侧代码段前后指定需要调优的范围。使用 msOpProf 工具进行算子上板调优时使用。

推荐使用 asc_prof_start 接口替代，该接口同时适用于 C 语言和 C++ 语言编程。MetricsProfStart/Stop 无参数，调用方式为在待调优代码段前后分别插入两个接口。

<!-- cannbot:related:start -->
## 相关

- [性能调优（调试与调优）](../../../../../guides/programming_guide/debug_and_tuning/performance_tuning.md)（`explains`）：性能调优指南说明如何把 kernel 侧采集标记接入上板测量和瓶颈分析。
- [MarkStamp](mark_stamp.md)（`related`）：PerformanceStats 提供区间统计，MarkStamp 提供离散事件标记；两者可组合定位算子时间线中的阶段边界。
- [asc_prof_start](../../../../utils_api/tuning_interface/asc_prof_start.md)（`related`）：性能统计说明性能统计接口集，包含 MetricsProfStart、MetricsProfStop 等性能指标采集接口。
- [MetricsProfStart](metrics_prof_start.md)（`same_topic`）：性能统计入口页说明 MetricsProfStart/Stop 的配对方式，并指出新代码优先使用 asc_prof_start/stop。
- [MetricsProfStop](metrics_prof_stop.md)（`same_topic`）：MetricsProfStop 关闭由 MetricsProfStart 开启的采样，缺少它会失去明确的测量区间。
<!-- cannbot:related:end -->
