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
