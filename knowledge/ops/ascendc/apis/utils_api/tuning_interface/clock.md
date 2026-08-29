---
type: API
title: Clock
description: SIMD和SIMT调试场景中提供Clock时间戳功能，记录从程序启动到调用时刻所经历的时钟周期数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/tuning_interface/clock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# clock

本接口在SIMD和SIMT调试场景中提供Clock时间戳功能，用于记录从程序启动到接口调用时刻所经历的时钟周期数（Cycle Count），便于精确分析执行延迟和性能瓶颈。

函数原型：__aicore__ inline uint64_t clock(void)；inline uint64_t clock(void)

返回值：从程序开始到调用时所经历的时钟周期数。

平台支持：Ascend 950PR/950DT、Atlas A3 训练/推理、Atlas A2 训练/推理系列支持，其他产品不支持。
约束：-   SIMT场景的支持情况如下：

    - Ascend 950PR/Ascend 950DT：支持。


    - Atlas A3 训练系列产品/Atlas A3 推理系列产品：不支持。


    - Atlas A2 训练系列产品/Atlas A2 推理系列产品：不支持。
需包含头文件 "utils/debug/asc_time.h"。
支持 SIMT 与 SIMD/SIMT 混合编程场景。
