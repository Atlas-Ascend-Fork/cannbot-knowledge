---
type: API
title: __cvta_generic_to_ubuf
description: 将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_conversion_functions/__cvta_generic_to_ubuf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __cvta_generic_to_ubuf

将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。
函数原型：size_t __cvta_generic_to_ubuf(const void* ptr)
返回值：输入指针指向Unified Buffer内存空间的地址值。
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [__ubuf__ 指针传普通形参导致编译失败](../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：__ubuf__ 指针传普通形参导致编译失败 与《__cvta_generic_to_ubuf》的实质衔接是：__ubuf__ 是指针类型的一部分，helper 形参、Load/Store、ReinterpretCast、地址空间转换与谓词必须保留相同 qualifier，不能隐式退化为普通 T*。
- [__isUbuf](../address_space_predicate_functions/_is_ubuf.md)（`related`）：《__isUbuf》处理“判断输入的指针是否指向Unified Buffer内存空间的地址。”。《__cvta_generic_to_ubuf》明确“将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。”，可直接用于核对SIMT UB 地址空间谓词、generic/ubuf 转换和指针形参限定合同。
- [__cvta_ubuf_to_generic](_cvta_ubuf_to_generic.md)（`same_topic`）：《__cvta_ubuf_to_generic》明确“将Unified Buffer内存空间的地址值转换为对应的指针并返回。”；它与《__cvta_generic_to_ubuf》的“将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。”在实际调用参数、数据流或结果校验上直接衔接。
- [地址空间转换函数](address_space_conversion_functions.md)（`same_topic`）：《地址空间转换函数》给出“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”；该约束/探针可直接复现、解释或前置验证《__cvta_generic_to_ubuf》中的“将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。”。
<!-- cannbot:related:end -->
