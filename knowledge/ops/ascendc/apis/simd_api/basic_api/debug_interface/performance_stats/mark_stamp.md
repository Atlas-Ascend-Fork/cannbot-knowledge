---
type: API
title: MarkStamp
description: 推荐使用asc_mark_stamp接口进行特定位置的标记，该接口同时适用于C语言和C++语言编程。 用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/performance_stats/MarkStamp.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MarkStamp

推荐使用asc_mark_stamp接口进行特定位置的标记，该接口同时适用于C语言和C++语言编程。 用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。

SIMD场景下，用户通过调用接口，用于在算子执行过程中标记特定位置，便于后期通过流水图分析代码执行路径与性能热点。

本接口组包含 asc_mark_stamp。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

约束：idx取值范围为[0,4095]。为方便从打点图中找到对应的代码，建议不要重复使用相同的idx。；如果在循环中增加了一个asc_mark_stamp指令，每次执行到指令时都会输出一个打点，且idx是相同的。；如果开发者在两个相邻的VF分别打标记，由于编译器可能会对VF A和VF B做融合，asc_mark_stamp1和asc_mark_stamp2则会被优化掉，不会输出打点。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
