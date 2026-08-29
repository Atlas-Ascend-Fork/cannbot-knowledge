---
type: API
title: GetShape
description: 需要包含的头文件为：#include "tensor_api/tensor.h"。 GetShape用于从Layout中提取Shape部分：
  - 不指定模板参数Is...：返回完整的Shape元组。 - 指定模板参数Is...：从Shape顶层tuple中选择对应索引的元素。指定单个索引时返回该元素；指定多个索引时返回由这些顶层元素组成的新tuple。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structure_TensorAPI/layout_structure/GetShape.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# GetShape

从 Layout 中提取 Shape 部分。不指定模板参数返回完整 Shape 元组；指定 Is... 从顶层 tuple 选择对应索引元素，单个索引返回该元素，多个索引返回新 tuple。头文件 `tensor_api/tensor.h`。仅 950 支持。

<!-- cannbot:related:start -->
## 相关

- [Layout](layout.md)（`related`）：“从 Layout 中提取 Shape 部分。不指定模板参数返回完整 Shape 元组；指定 Is... 从顶层 tuple 选择对应索引元素，单个索引返回该元素，多个索引返回新 tuple。头文件 `tensor_api/tensor.h`。仅 950 支持。”与“试验接口。Layout<Shape, Stride> 是描述多维张量内存布局的模板类，通过编译时 Shape（逻辑形状）和 Stride（各维度内存步长）实现逻辑坐标到一维地址的映射，编译时完成计算降低运行时开销。头文件 `tensor_api/tensor.h`。”提供双方正文证据。GetShape 从 Layout 模板对象抽取其 Shape 组成，Layout 卡界定 Shape 与 Stride 如何共同描述地址映射；二者属于同一次布局检查的对象与访问器。
<!-- cannbot:related:end -->
