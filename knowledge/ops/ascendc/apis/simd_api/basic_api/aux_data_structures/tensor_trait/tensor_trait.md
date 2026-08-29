---
type: API
title: TensorTrait
description: TensorTrait 辅助数据结构用于承载张量布局信息，提供 GetLayout、SetLayout、MakeTensorTrait 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorTrait/TensorTrait.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TensorTrait

TensorTrait 用于承载张量的 Layout 布局信息，是矢量计算接口中描述张量排布属性的辅助数据结构。
提供构造函数创建对象，GetLayout/SetLayout 查询与设置布局，MakeTensorTrait 构建布局对象，is_tensorTrait 进行类型判断。
