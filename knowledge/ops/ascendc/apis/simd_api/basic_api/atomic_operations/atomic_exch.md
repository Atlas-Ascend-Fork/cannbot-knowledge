---
type: API
title: AtomicExch
description: 对GM地址执行原子交换，将输入标量值写入并返回修改前的旧值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/AtomicExch.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AtomicExch

在指定GM地址上进行原子交换操作。将address指向的GM地址上的旧值与输入值进行原子交换运算，将结果写回GM地址，返回修改前的旧值。仅Ascend 950PR/950DT支持。

函数原型通过模板参数T指定数据类型（支持int32_t/uint32_t/int64_t/uint64_t/float等）。接口参数：address为GM地址指针；value为输入标量值。返回值为修改前的旧值。

约束：仅支持标量操作；遵循通用地址对齐约束。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [重复目标随机写丢失 — 在 UB 内按序合并后 DMA 写回](../../../../runbooks/precision/repeated_overwrite_updates_need_ordered_ub_merge.md)（`exemplifies`）：AtomicExch 是卡内列出的硬件原子替代路线之一，但原子交换本身不定义多个 k 的 winner 顺序。
- [AscAtomicExch](../../c_api/scalar_compute/asc_atomic_exch.md)（`related`）：基础 C++ AtomicExch 提供同一 GM 原子交换契约，可与 C Scalar 版本按语言接口选择。
- [AtomicCas](atomic_cas.md)（`related`）：《AtomicExch》处理“对GM地址执行原子交换，将输入标量值写入并返回修改前的旧值。”。《AtomicCas》明确“对GM地址执行原子比较交换：旧值与value1相等时写入value2，否则不变，返回旧值。”，可直接用于核对AtomicExch 的 C/C++ 入口及与 AtomicCas 的原子更新语义差异。
- [asc_atomic_exch](../../../simt_api/atomic_operations/asc_atomic_exch.md)（`same_topic`）：《AtomicExch》处理“对GM地址执行原子交换，将输入标量值写入并返回修改前的旧值。”。《asc_atomic_exch》明确“对Unified Buffer或Global Memory地址做原子赋值操作，即将指定数据赋值到Unified Buffer或Global Memory地址中。”，可直接用于核对AtomicExch 的 C/C++ 入口及与 AtomicCas 的原子更新语义差异。
<!-- cannbot:related:end -->
