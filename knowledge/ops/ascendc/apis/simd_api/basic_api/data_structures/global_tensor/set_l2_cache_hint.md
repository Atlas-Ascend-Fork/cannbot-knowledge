---
type: API
title: SetL2CacheHint
description: 设置GlobalTensor是否启用L2 Cache，默认启用L2 Cache。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetL2CacheHint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetL2CacheHint

设置 GlobalTensor 是否启用 L2 Cache，默认启用。函数签名为 template<CacheRwMode rwMode = CacheRwMode::RW> void SetL2CacheHint(CacheMode mode)。
参数 mode 指定 L2 Cache 模式：CACHE_MODE_DISABLE 禁用、CACHE_MODE_NORMAL 普通模式（默认，容量满时触发置换）、CACHE_MODE_PERSISTENT 驻留模式（开发中，暂不支持）。
模板参数 rwMode 为读写模式预留参数（READ/WRITE/RW），使用默认值即可。
当特定 GlobalTensor 启用 L2 Cache 后性能反而下降时可手动禁用，例如仅对单次读取的 Tensor 关闭缓存以避免额外搬运开销。
支持 Ascend 950PR/950DT、Atlas A2 与 Atlas A3 系列产品。
