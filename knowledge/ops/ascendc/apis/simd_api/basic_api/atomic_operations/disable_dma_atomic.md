---
type: API
title: DisableDmaAtomic
description: 关闭数据搬运随路原子操作，后续搬运时GM原始数据将被新数据完全覆盖。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/DisableDmaAtomic.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DisableDmaAtomic

禁用DMA搬运时的随路原子操作。调用后，后续从UB/L0C/L1到GM的DataCopy搬运不再执行原子操作，恢复为普通覆盖写入。

函数原型：__aicore__ inline void DisableDmaAtomic()。参数：无。约束：与SetAtomicAdd/SetAtomicMax等配合使用，成对调用。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [SetAtomicAdd](set_atomic_add.md)（`related`）：SetAtomicAdd 开启后续搬出随路原子加，DisableDmaAtomic 用于在该段结束后恢复普通覆盖写；两者须成对界定作用域。
- [SetAtomicMax](set_atomic_max_isasi.md)（`related`）：SetAtomicMax 开启随路取大，DisableDmaAtomic 结束该状态，否则后续 DataCopy 会继续原子合并。
- [SetAtomicMin](set_atomic_min_isasi.md)（`related`）：SetAtomicMin 开启随路取小，DisableDmaAtomic 将后续 UB/L0C/L1→GM 恢复为覆盖写。
- [SetAtomicType](set_atomic_type.md)（`related`）：DisableDmaAtomic 负责结束 SetAtomicType 建立的 DMA 原子状态，避免后续搬运错误继承原子语义。
- [关键特性说明（原子操作）](key_features.md)（`related`）：关键特性明确把 DisableDmaAtomic 作为浮点 DMA 原子累加结束和规避状态泄漏的动作。
- [原子操作概述](atomic_operations_overview.md)（`related`）：概述要求 DMA 原子操作完成后关闭原子状态，DisableDmaAtomic 是避免状态泄漏到后续搬出的收尾动作。
<!-- cannbot:related:end -->
