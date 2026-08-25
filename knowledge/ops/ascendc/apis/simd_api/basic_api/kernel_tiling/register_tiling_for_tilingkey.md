---
type: API
title: REGISTER_TILING_FOR_TILINGKEY
description: 用于在kernel侧注册与TilingKey相匹配的TilingData自定义结构体；该接口需提供一个逻辑表达式，逻辑表达式以字符串“TILING_KEY_VAR”代指实际TilingKey，表达TilingKey所满足的范围。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_TILING_FOR_TILINGKEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# REGISTER_TILING_FOR_TILINGKEY

在 kernel 侧注册与 TilingKey 相匹配的 TilingData 结构体。提供逻辑表达式（以 TILING_KEY_VAR 代指实际 TilingKey）表达 TilingKey 满足的范围。支持 950/a2/a3。
