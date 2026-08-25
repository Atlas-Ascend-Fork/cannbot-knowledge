---
type: API
title: GlobalTensor构造函数
description: GlobalTensor构造函数。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GlobalTensor构造函数

GlobalTensor 默认构造函数，创建空的 GlobalTensor 对象，后续通过 SetGlobalBuffer 设置 GM 地址和大小。模板参数 T 为数据类型。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [GlobalTensor简介](global_tensor_intro.md)（`same_topic`）：《GlobalTensor构造函数》明确“GlobalTensor构造函数。”；它与《GlobalTensor简介》的“GlobalTensor用来存放Global Memory（外部存储）的全局数据。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
