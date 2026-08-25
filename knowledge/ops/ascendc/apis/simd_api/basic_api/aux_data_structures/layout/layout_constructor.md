---
type: API
title: Layout构造函数
description: 根据输入的Shape和Stride对象，实例化Layout对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---


# Layout构造函数

Layout提供多种构造方式：默认构造（空Layout）、通过shape和stride构造、通过其他Layout拷贝构造等。构造后可通过SetShape/SetStride等方法修改属性。Layout构造参数可包含shape数组、stride数组、format格式等。构造的Layout用于描述Tensor的数据排布，传递给TensorDesc或TensorTrait使用。
