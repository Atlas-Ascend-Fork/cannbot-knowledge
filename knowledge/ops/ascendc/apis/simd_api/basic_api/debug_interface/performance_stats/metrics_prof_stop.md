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
