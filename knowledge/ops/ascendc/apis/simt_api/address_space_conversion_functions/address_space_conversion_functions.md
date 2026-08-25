---
type: API
title: 地址空间转换函数
description: SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。
tags: [task.lookup, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/address_space_conversion_functions/address_space_conversion_functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 地址空间转换函数

-   **__cvta_generic_to_global**

-   **__cvta_generic_to_ubuf**

-   **__cvta_generic_to_local**

-   **__cvta_global_to_generic**

-   **__cvta_ubuf_to_generic**

-   **__cvta_local_to_generic**

<!-- cannbot:related:start -->
## 相关

- [Device helper 必须保留 GM 地址空间](../../../runbooks/compilation/device_helper_preserves_gm_address_space.md)（`exemplifies`）：《地址空间转换函数》处理“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”。《Device helper 必须保留 GM 地址空间》提供“Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。”，其具体合同或探针直接接入SIMT 地址空间转换与谓词验证、helper 形参地址限定合同。
- [__ubuf__ 指针传普通形参导致编译失败](../../../runbooks/compilation/ubuf_pointer_preserves_address_space.md)（`exemplifies`）：《地址空间转换函数》处理“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”。《__ubuf__ 指针传普通形参导致编译失败》提供“Ascend C 地址空间是类型的一部分；__ubuf__ 指针不能隐式绑定到普通 T* 形参，未使用参数应删除或按真实地址空间声明。”，其具体合同或探针直接接入SIMT 地址空间转换与谓词验证、helper 形参地址限定合同。
- [__cvta_generic_to_global](_cvta_generic_to_global.md)（`related`）：《__cvta_generic_to_global》的任务是“将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。”。《地址空间转换函数》具体提供“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”，它直接用于generic 指针转 Global 地址、反向转换和 GM 地址空间验证。
- [__cvta_generic_to_ubuf](_cvta_generic_to_ubuf.md)（`same_topic`）：《地址空间转换函数》给出“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”；该约束/探针可直接复现、解释或前置验证《__cvta_generic_to_ubuf》中的“将输入的指针转换为其指向的Unified Buffer内存空间的地址值并返回。”。
- [__cvta_global_to_generic](_cvta_global_to_generic.md)（`same_topic`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《地址空间转换函数》明确提供“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [地址空间谓词函数](../address_space_predicate_functions/address_space_predicate_functions.md)（`same_topic`）：《地址空间转换函数》处理“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”。《地址空间谓词函数》提供“SIMT API地址空间谓词函数汇总，提供判断指针是否指向Global、UBuf、Local地址空间的断言能力。”，其具体合同或探针直接接入SIMT 地址空间转换与谓词验证、helper 形参地址限定合同。
<!-- cannbot:related:end -->
