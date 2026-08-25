---
type: API
title: TensorTrait构造函数
description: 根据输入的Layout对象，实例化TensorTrait对象。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/TensorTrait_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# TensorTrait构造函数

TensorTrait提供多种构造方式：默认构造、通过TensorDesc和Layout构造、拷贝构造等。构造参数可包含TensorDesc信息、Layout信息等。构造的TensorTrait用于描述Tensor的完整信息（含排布），传递给高阶API使用。
