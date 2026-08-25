---
type: API
title: TQueBind
description: TQueBind接口索引页，包含简介、构造函数、AllocTensor/FreeTensor、EnQue/DeQue及BufHandle管理。
tags: [task.lookup, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQueBind/TQueBind.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# TQueBind

TQueBind绑定源逻辑位置和目的逻辑位置，根据两端位置确定内存分配和同步事件插入。TQue是TQueBind的简化模式，常规矢量编程使用TQue即可；涉及特殊数据通路（如VECIN→VECOUT、VECOUT→A1/B1/C1、CO2→VECIN）时需使用TQueBind。
模板参数src/dst支持VECIN/VECOUT/A1/A2/B1/B2/CO1/CO2及其组合，depth一般不超过4，mask控制ND到NZ格式转换。
Cube相关数据通路建议使用Matmul等高阶API实现，直接使用TQueBind控制较为复杂。提供AllocTensor/FreeTensor/EnQue/DeQue队列操作及FreeAllEvent、InitBufHandle/InitStartBufHandle等Buffer管理接口。
