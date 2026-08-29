---
type: API
title: SetAtomicType
description: 通过模板参数设定后续原子操作的数据类型。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicType

设置DMA搬运时的随路原子操作类型。可配置为原子加、原子最大值、原子最小值等。

函数原型：template <typename T> __aicore__ inline void SetAtomicType(AtomicType atomicType)。模板参数T指定数据类型。参数：atomicType为原子操作类型枚举。约束：与DisableDmaAtomic配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [DisableDmaAtomic](disable_dma_atomic.md)（`same_topic`）：函数原型：template <typename T> __aicore__ inline void SetAtomicType(AtomicType atomicType)。模板参数T指定数据类型。参数：atomicType为原子操作类型枚举。约束：与DisableDmaAtomic配合使用。头文件：basic_api/kernel_operator_atomic_intf.h。 调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。 SetAtomicType 选择随路原子类型，DisableDmaAtomic 在使用后清状态，避免后续搬运继续执行原子操作。
<!-- cannbot:related:end -->
