---
type: API
title: 关闭ASCENDC_DUMP说明
description: 调试接口（如本章的上板打印、异常检测接口）开启后会对算子性能产生一定影响，通常在调测阶段使用，生产环境建议关闭。ASCENDC_DUMP宏定义是控制调试接口打印的开关。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/disable_ascendc_dump.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 关闭ASCENDC_DUMP说明

ASCENDC_DUMP 宏定义控制调试接口（上板打印、异常检测等）的打印开关。调测阶段开启，生产环境建议关闭以避免性能影响。关闭方式：在编译选项中不定义 ASCENDC_DUMP 宏或将其设为 0。

<!-- cannbot:related:start -->
## 相关

- [asc_dump](../../../utils_api/tuning_interface/asc_dump.md)（`same_topic`）：关闭方式：在编译选项中不定义 ASCENDC_DUMP 宏或将其设为 0。；生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。；两卡描述同一 asc_dump 调试能力的生产关闭开关，一端是开关说明，一端是被控制接口的运行边界。
<!-- cannbot:related:end -->
