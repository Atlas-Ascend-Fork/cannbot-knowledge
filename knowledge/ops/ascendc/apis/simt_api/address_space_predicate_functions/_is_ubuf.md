---
type: API
title: __isUbuf
description: 判断输入的指针是否指向Unified Buffer内存空间的地址。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_predicate_functions/__isUbuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isUbuf

判断输入的指针是否指向Unified Buffer内存空间的地址。
函数原型：unsigned int __isUbuf(const void* ptr)
返回值：如果输入的指针指向Unified Buffer内存空间的地址，则返回1，否则返回0。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等
