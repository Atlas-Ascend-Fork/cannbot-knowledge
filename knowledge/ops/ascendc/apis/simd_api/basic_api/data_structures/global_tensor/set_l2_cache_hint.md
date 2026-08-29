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

<!-- cannbot:related:start -->
## 相关

- [设置合理的L2 CacheMode](../../../../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`explains`）：当特定 GlobalTensor 启用 L2 Cache 后性能反而下降时可手动禁用，例如仅对单次读取的 Tensor 关闭缓存以避免额外搬运开销。；开发者可以针对访问的数据设置其CacheMode，对于只访问一次的Global Memory数据设置其访问状态为不进入L2 Cache，这样可以更加高效的利用L2 Cache缓存需要重复读取的数据，避免一次性访问的数据替换有效数据。。API 卡给出禁用入口，指南解释一次性数据污染缓存并替换有效数据的性能机制。
- [高阶性能打磨](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/add_vector_operator/advanced_optimization.md)（`explains`）：“原理：L2 Cache是AI Core和HBM之间的缓存层，适合需要重复访问的数据。对于Add算子这种流式访问场景（输入数据只读取一次），数据经过L2 Cache反而会占用Cache空间（Cache污染），增加搬运延时。通过SetL2CacheHint设置CACHE_MODE_DISABLE，让数据绕过L2 Cache直接从GM载入UB。”给出 Add 单次读取输入发生 L2 污染时的实测优化调用；“当特定 GlobalTensor 启用 L2 Cache 后性能反而下降时可手动禁用，例如仅对单次读取的 Tensor 关闭缓存以避免额外搬运开销。”定义该 API 正适用于只访问一次的 GlobalTensor。两端把性能症状、选型条件和具体 CACHE_MODE_DISABLE 接口连成可复用步骤。
<!-- cannbot:related:end -->
