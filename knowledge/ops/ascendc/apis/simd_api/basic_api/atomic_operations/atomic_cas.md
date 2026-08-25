---
type: API
title: AtomicCas
description: 对GM地址执行原子比较交换：旧值与value1相等时写入value2，否则不变，返回旧值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/AtomicCas.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AtomicCas

在指定GM地址上进行原子比较并交换操作。将address指向的GM地址上的旧值与输入值进行原子比较并交换运算，将结果写回GM地址，返回修改前的旧值。仅Ascend 950PR/950DT支持。

函数原型通过模板参数T指定数据类型（支持int32_t/uint32_t/int64_t/uint64_t/float等）。接口参数：address为GM地址指针；value为输入标量值。返回值为修改前的旧值。

约束：仅支持标量操作；遵循通用地址对齐约束。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：该指南解释并发读改写的数据竞争以及必须使用原子的场景，为 AtomicCas 何时用于状态抢占和条件更新提供使用边界。
- [AtomicExch](atomic_exch.md)（`related`）：《AtomicExch》处理“对GM地址执行原子交换，将输入标量值写入并返回修改前的旧值。”。《AtomicCas》明确“对GM地址执行原子比较交换：旧值与value1相等时写入value2，否则不变，返回旧值。”，可直接用于核对AtomicExch 的 C/C++ 入口及与 AtomicCas 的原子更新语义差异。
- [原子操作概述](atomic_operations_overview.md)（`related`）：概述把 CAS 列为标量即时原子操作并说明其返回旧值语义，AtomicCas 页给出具体比较交换契约。
- [AscAtomicCas](../../c_api/scalar_compute/asc_atomic_cas.md)（`same_topic`）：AtomicCas说明对GM地址执行原子比较交换：旧值与value1相等时写入value2，否则不变，返回旧值。
- [asc_atomic_cas](../../../simt_api/atomic_operations/asc_atomic_cas.md)（`same_topic`）：C++ AtomicCas 与 SIMT asc_atomic_cas 提供同一 CAS 原语，可据 Kernel 编程模型选择。
<!-- cannbot:related:end -->
