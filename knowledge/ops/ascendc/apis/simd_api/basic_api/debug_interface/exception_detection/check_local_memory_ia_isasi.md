---
type: API
title: CheckLocalMemoryIA
description: 检查设定范围内UB读写行为的调试接口，有设定范围的读写行为会触发EXCEPTION报错。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/exception_detection/CheckLocalMemoryIA_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# CheckLocalMemoryIA

检查设定范围内 UB 读写行为的调试接口。设定范围内的读写行为会触发 EXCEPTION 报错，用于检测越界访问。参数含检查的 UB 地址范围和读写模式。仅 a2/a3 支持。
