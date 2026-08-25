---
type: API
title: __isLocal
description: 判断输入的指针是否指向栈空间的地址。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.implementation.masking]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_predicate_functions/__isLocal.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __isLocal

判断输入的指针是否指向栈空间的地址。
函数原型：unsigned int __isLocal(const void* ptr)
返回值：如果输入的指针指向栈空间的地址，则返回1，否则返回0。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [CheckLocalMemoryIA](../../simd_api/basic_api/debug_interface/exception_detection/check_local_memory_ia_isasi.md)（`related`）：CheckLocalMemoryIA 与《__isLocal》的实质衔接是：CheckLocalMemoryIA 通过保留的 UB 地址范围触发异常，需结合 LocalMemAllocator、地址空间转换与 ASCENDC_DUMP 调试开关定位本地内存越界。
- [__cvta_generic_to_local](../address_space_conversion_functions/_cvta_generic_to_local.md)（`related`）：__isLocal 先判断 generic 指针是否指向栈空间，generic_to_local 再把该指针转换为 local raw address；二者形成判定后转换的安全链。
- [__cvta_local_to_generic](../address_space_conversion_functions/_cvta_local_to_generic.md)（`related`）：local_to_generic 从栈地址值恢复指针且不校验有效性，__isLocal 可用于恢复后验证地址空间，形成双向转换的校验闭环。
- [__isGlobal](_is_global.md)（`related`）：__isLocal 与 __isGlobal 是对同一 generic 指针的互斥地址空间判别，可在分派访问路径前区分栈空间和 GM。
<!-- cannbot:related:end -->
