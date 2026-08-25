---
type: API
title: __cvta_generic_to_local
description: 将输入的指针转换为其指向的栈空间的地址值并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_conversion_functions/__cvta_generic_to_local.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __cvta_generic_to_local

将输入的指针转换为其指向的栈空间的地址值并返回。
函数原型：size_t __cvta_generic_to_local(const void* ptr)
返回值：输入指针指向栈空间的地址值。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CheckLocalMemoryIA](../../simd_api/basic_api/debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《__cvta_generic_to_local》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [__isLocal](../address_space_predicate_functions/_is_local.md)（`related`）：__isLocal 先判断 generic 指针是否指向栈空间，generic_to_local 再把该指针转换为 local raw address；二者形成判定后转换的安全链。
- [__cvta_local_to_generic](_cvta_local_to_generic.md)（`same_topic`）：焦点把通用指针还原为 local 栈地址值，候选把 local 地址值重新转换为通用指针，形成同一地址空间映射的相反方向。
<!-- cannbot:related:end -->
