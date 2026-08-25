---
type: API
title: __cvta_local_to_generic
description: 将栈空间的地址值转换为对应的指针并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_conversion_functions/__cvta_local_to_generic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __cvta_local_to_generic

将栈空间的地址值转换为对应的指针并返回。
函数原型：void* __cvta_local_to_generic(size_t rawbits)
返回值：指向输入栈空间的指针。该接口不校验输入是否为有效栈空间地址。异常场景示例说明如下：
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
