---
type: API
title: __cvta_global_to_generic
description: 将Global Memory内存空间的地址值转换为对应的指针并返回。
tags: [task.lookup, topic.implementation.api_layer.simt_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_conversion_functions/__cvta_global_to_generic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# __cvta_global_to_generic

将Global Memory内存空间的地址值转换为对应的指针并返回。
函数原型：void* __cvta_global_to_generic(size_t rawbits)
返回值：指向Global Memory内存空间的指针。该接口不校验输入是否为有效Global Memory地址。异常场景示例说明如下：
约束：SIMD与SIMT混合编程场景不支持使用该接口。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Device helper 必须保留 GM 地址空间](../../../runbooks/compilation/device_helper_preserves_gm_address_space.md)（`exemplifies`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《Device helper 必须保留 GM 地址空间》明确提供“Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [__isGlobal](../address_space_predicate_functions/_is_global.md)（`related`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《__isGlobal》明确提供“判断输入的指针是否指向Global Memory内存空间的地址。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [__cvta_generic_to_global](_cvta_generic_to_global.md)（`same_topic`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《__cvta_generic_to_global》明确提供“将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [地址空间转换函数](address_space_conversion_functions.md)（`same_topic`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《地址空间转换函数》明确提供“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
<!-- cannbot:related:end -->
