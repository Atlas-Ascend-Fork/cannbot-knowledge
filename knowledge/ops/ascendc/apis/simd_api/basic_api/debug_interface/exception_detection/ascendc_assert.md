---
type: API
title: AscendcAssert
description: CPU/NPU域断言接口，当断言条件不满足时输出断言信息并格式化打印，主要用于调试阶段。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/ascendc_assert.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# AscendcAssert

CPU/NPU 域断言接口。断言条件不满足时输出断言信息并格式化打印，NPU 模式下还会触发 Trap 中断。参数 condition 为断言条件，format 为格式化字符串。仅调试阶段使用。支持 950/a2/a3。
