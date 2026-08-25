---
type: API
title: GlobalTensor
description: GlobalTensor 数据结构接口集，提供全局张量管理能力，含构造函数、SetGlobalBuffer、GetPhyAddr、GetValue 等。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GlobalTensor

GlobalTensor 用于管理 GM（Global Memory）侧的全局张量，提供 SetGlobalBuffer 绑定物理缓冲区，GetValue/SetValue/operator[]/operator() 进行元素读写，GetSize/SetShapeInfo/GetShapeInfo 管理形状与大小，GetPhyAddr 获取物理地址。ReinterpretCast 支持类型重解释，SetL2CacheHint 可设置 L2 Cache 访问提示以优化搬运性能。
