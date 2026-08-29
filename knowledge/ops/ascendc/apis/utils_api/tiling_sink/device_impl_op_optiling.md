---
type: API
title: DEVICE_IMPL_OP_OPTILING
description: 在Tiling下沉场景中，该宏定义用于生成Tiling下沉的注册类，再通过调用注册类的成员函数来注册需要下沉的Tiling函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_sink/DEVICE_IMPL_OP_OPTILING.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# DEVICE_IMPL_OP_OPTILING

## 功能说明
在Tiling下沉场景中，该宏定义用于生成Tiling下沉的注册类，再通过调用注册类的成员函数来注册需要下沉的Tiling函数。
## 函数原型
## 参数说明
DEVICE_IMPL_OP_OPTILING参数说明
Tiling成员函数参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [开启Tiling下沉](../../../guides/programming_guide/advanced_programming/operator_graph_development/enable_tiling_sink.md)（`explains`）：完成下沉Tiling函数注册：包含device_op_impl_registry.h头文件，使用宏DEVICE_IMPL_OP_OPTILING进行注册。；在Tiling下沉场景中，该宏定义用于生成Tiling下沉的注册类，再通过调用注册类的成员函数来注册需要下沉的Tiling函数。。指南给出 DEVICE_IMPL_OP_OPTILING 的注册步骤，接口卡解释该宏生成注册类并绑定下沉 Tiling 函数的具体作用。
<!-- cannbot:related:end -->
