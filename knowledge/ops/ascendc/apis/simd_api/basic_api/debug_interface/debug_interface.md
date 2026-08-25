---
type: API
title: 调试接口
description: AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/debug_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 调试接口

AscendC 调试接口总览，涵盖上板打印（NPU 运行时输出调试信息）、异常检测（断言与 trap）、CPU 孪生调试（CPU 侧模拟核函数）、性能统计（算子耗时与流水分析）四类调试能力，以及关闭 ASCENDC_DUMP 的说明。开发者可按调试阶段选择对应工具：CPU 侧验证逻辑，上板侧定位真实硬件问题。
