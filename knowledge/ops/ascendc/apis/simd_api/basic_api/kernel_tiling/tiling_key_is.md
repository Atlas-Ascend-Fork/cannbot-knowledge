---
type: API
title: TILING_KEY_IS
description: 在核函数中判断本次执行时的tiling_key是否等于host侧运行时设置的某个key，从而标识tiling_key==key的一条kernel分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/TILING_KEY_IS.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TILING_KEY_IS

在核函数中判断本次执行的 tiling_key 是否等于 host 侧设置的某个 key，标识 tiling_key==key 的 kernel 分支。支持 950/a2/a3。
