---
type: API
title: asc_vf_call
description: 在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/vf_call/asc_vf_call.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# asc_vf_call

在SIMD编程场景下使用。用于启动SIMD VF（Vector Function）子任务。

参数：funcPtr: 用于指定SIMD入口核函数。；Args: 定义可变参数，用于传递实参到SIMD入口核函数。；args(输入): 可变参数，用于传递实参到SIMD入口核函数。

约束：-   asc_vf_call启动SIMD VF子任务时，子任务函数不能是类的成员函数，推荐使用普通函数或类静态函数，且入口函数必须使用__simd_vf__修饰宏。
-   asc_vf_call启动SIMD VF子任务时，入参仅支持Ascend C的内置数据类型（half、int32_t、uint32_t、float等）及其组成的指针、数组、结构体类型，且指针类型必须指向UB内存。

仅 Ascend 950PR/Ascend 950DT 支持。
