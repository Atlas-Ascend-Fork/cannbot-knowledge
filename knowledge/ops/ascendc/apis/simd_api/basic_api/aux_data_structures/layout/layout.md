---
type: API
title: Layout（辅助数据结构）
description: Layout 辅助数据结构用于描述张量数据排布，提供构造函数、Shape/Stride 操作与 MakeLayout 等接口。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/aux_data_structures/Layout/Layout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# Layout（辅助数据结构）

Layout 用于描述张量数据在内存中的排布方式，包含 Shape、Stride 等核心属性。
提供构造函数创建 Layout 对象，GetShape/GetStride 查询排布信息，MakeShape/MakeStride/MakeLayout 构建排布对象，以及 is_layout 进行类型判断。
支持运算符重载，便于排布对象的比较与赋值操作。
