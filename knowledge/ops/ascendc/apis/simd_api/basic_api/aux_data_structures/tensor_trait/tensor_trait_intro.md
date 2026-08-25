---
type: API
title: TensorTrait简介
description: TensorTrait数据结构是描述Tensor相关信息的基础模板类，包含Tensor的数据类型、逻辑位置和Layout内存布局。借助模板元编程技术，该类在编译时完成计算和代码生成，从而降低运行时开销。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/TensorTrait_intro.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# TensorTrait简介

TensorTrait是Tensor特性描述结构体，在TensorDesc基础上增加了Layout信息，提供更完整的Tensor描述。TensorTrait包含shape、data type、layout和地址等信息。TensorTrait提供GetLayout获取排布信息、SetLayout设置排布等接口。通过MakeTensorTrait构造，与TensorDesc相比增加了Layout维度的描述能力。常用于需要精确控制Tensor排布的高级场景。
