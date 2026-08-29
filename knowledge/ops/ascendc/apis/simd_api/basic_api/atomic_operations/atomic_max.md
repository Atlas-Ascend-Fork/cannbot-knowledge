---
type: API
title: AtomicMax
description: 对GM地址上的值执行原子取大操作，将旧值与输入标量比较后写入较大值，返回旧值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/AtomicMax.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AtomicMax

在指定GM地址上进行原子取最大值操作。将address指向的GM地址上的旧值与输入值进行原子取最大值运算，将结果写回GM地址，返回修改前的旧值。仅Ascend 950PR/950DT支持。

函数原型通过模板参数T指定数据类型（支持int32_t/uint32_t/int64_t/uint64_t/float等）。接口参数：address为GM地址指针；value为输入标量值。返回值为修改前的旧值。

约束：仅支持标量操作；遵循通用地址对齐约束。头文件：basic_api/kernel_operator_atomic_intf.h。
