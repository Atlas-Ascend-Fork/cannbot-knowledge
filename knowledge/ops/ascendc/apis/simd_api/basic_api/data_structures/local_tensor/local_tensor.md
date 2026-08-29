---
type: API
title: LocalTensor
description: LocalTensor 数据结构接口集，提供 UB 侧局部张量管理能力，含构造函数、SetValue、GetValue、GetSize 等。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/LocalTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LocalTensor

LocalTensor 用于管理 UB（Unified Buffer）侧的局部张量，是矢量计算的主要数据载体。提供 SetValue/GetValue/operator[]/operator() 元素读写，SetSize/GetSize/SetShapeInfo/GetShapeInfo 形状管理，GetPhyAddr/GetPosition/GetLength 地址与位置查询，ReinterpretCast 类型重解释。ToFile/Print 用于调试输出，SetUserTag 用于设置调试标签。
