---
type: API
title: VF调用
description: Reg矢量计算VF调用接口索引页，包含asc_vf_call。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/vf_call/vf_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# VF调用

提供 asc_vf_call 接口，用于在 SIMD 编程场景下启动 SIMD VF（Vector Function）子任务。通过模板参数 funcPtr 指定入口核函数，可变参数 Args 传递实参。

约束：子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，入口函数必须使用 __simd_vf__ 修饰；入参仅支持 Ascend C 内置数据类型及其指针、数组、结构体，指针必须指向 UB 内存。仅 Ascend 950PR/Ascend 950DT 支持。
