---
type: API
title: 原子操作
description: AscendC 矢量计算基础 API 的原子操作接口集，包含 SetAtomicAdd、SetAtomicType、AtomicAdd、AtomicCas 等原子算子配置与计算接口。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/atomic_operations.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 原子操作

Ascend C 矢量计算基础 API 原子操作接口集，提供对 Global Memory 的原子读改写操作，用于多核并发场景下的数据一致性保障。
配置类接口包括 SetAtomicAdd、SetAtomicType、DisableDmaAtomic，以及 ISASI 专属的 SetAtomicMax/SetAtomicMin/SetStoreAtomicConfig/GetStoreAtomicConfig。
计算类接口包括 AtomicAdd、AtomicMin、AtomicMax、AtomicCas、AtomicExch，分别支持原子加、最小、最大、比较交换与交换操作。
原子操作在相同核函数内部维持状态直到被改变，跨核函数不继承状态。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](../../c_api/simd_atomic/asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《原子操作》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [原子操作边界值汇总（附录）](../../../appendix/atomic_operations_interface_boundary_value_summary.md)（`related`）：原子操作 与《原子操作边界值汇总（附录）》的实质衔接是：原子操作总览与 CAS/Add/Exch/Min/Max 和 store atomic 配置共同界定并发更新选择。
- [关键特性说明（原子操作）](key_features.md)（`same_topic`）：原子操作 与《关键特性说明（原子操作）》的实质衔接是：原子操作总览与 CAS/Add/Exch/Min/Max 和 store atomic 配置共同界定并发更新选择。
<!-- cannbot:related:end -->
