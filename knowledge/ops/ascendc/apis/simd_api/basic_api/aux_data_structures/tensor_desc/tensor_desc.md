---
type: API
title: TensorDesc
description: TensorDesc 辅助数据结构用于描述张量描述信息，提供 SetShapeAddr、GetDim、GetShape、GetDataPtr 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/TensorDesc/TensorDesc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# TensorDesc

TensorDesc 用于描述张量的形状与数据指针信息，是矢量计算接口中传递张量元数据的辅助数据结构。
提供构造与析构函数管理生命周期，SetShapeAddr 设置形状与数据地址，GetDim/GetIndex/GetShape 查询维度与形状信息，GetDataPtr/GetDataObj 获取数据指针与数据对象。
