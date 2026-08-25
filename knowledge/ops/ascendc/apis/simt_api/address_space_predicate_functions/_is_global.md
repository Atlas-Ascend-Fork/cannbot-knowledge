---
type: API
title: __isGlobal
description: 判断输入的指针是否指向Global Memory内存空间的地址。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_predicate_functions/__isGlobal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isGlobal

判断输入的指针是否指向Global Memory内存空间的地址。
函数原型：unsigned int __isGlobal(const void* ptr)
返回值：如果输入的指针指向Global Memory内存空间的地址，则返回1，否则返回0。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__cvta_generic_to_global](../address_space_conversion_functions/_cvta_generic_to_global.md)（`related`）：《__cvta_generic_to_global》的任务是“将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。”。《__isGlobal》具体提供“判断输入的指针是否指向Global Memory内存空间的地址。”，它直接用于generic 指针转 Global 地址、反向转换和 GM 地址空间验证。
- [__cvta_global_to_generic](../address_space_conversion_functions/_cvta_global_to_generic.md)（`related`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《__isGlobal》明确提供“判断输入的指针是否指向Global Memory内存空间的地址。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [__isLocal](_is_local.md)（`related`）：__isLocal 与 __isGlobal 是对同一 generic 指针的互斥地址空间判别，可在分派访问路径前区分栈空间和 GM。
<!-- cannbot:related:end -->
