---
type: API
title: 废弃接口
description: 废弃接口索引页，汇总矢量计算asc_abs_sync与原子操作asc_set_atomic_add_int等已废弃接口。
tags: [task.lookup, topic.quality.compatibility.deprecation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/deprecated_interface/deprecated_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# 废弃接口（C API）

SIMD C API已废弃接口集合，不建议在新算子开发中使用。包含两类：矢量计算类废弃接口asc_abs_sync（同步模式的绝对值计算，已被异步接口asc_abs替代，使用异步接口可避免不必要的同步等待）和原子操作类废弃接口asc_set_atomic_add_int（原子加设置接口，已被新的原子操作机制替代）。使用废弃接口可能导致兼容性问题，开发者应查阅对应替代接口的文档。
