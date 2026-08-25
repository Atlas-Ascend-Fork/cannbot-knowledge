---
type: API
title: DumpAccChkPoint
description: 打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/onboard_print/DumpAccChkPoint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# DumpAccChkPoint

打印指定 Tensor 内容并支持自定义标签。区别于 DumpTensor，支持指定偏移位置开始打印。参数含 Tensor、偏移量、打印元素数和自定义标签字符串。需开启 ASCENDC_DUMP 宏。支持 950/a2/a3。
