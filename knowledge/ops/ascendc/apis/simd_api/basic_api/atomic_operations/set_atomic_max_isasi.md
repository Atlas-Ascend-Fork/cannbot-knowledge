---
type: API
title: SetAtomicMax
description: 对后续搬运到GM的数据开启原子取大，将拷贝内容与GM已有值比较后写入最大值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicMax_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicMax

设置DMA搬运时的随路原子操作为取最大值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最大值（旧值和新值中的最大值）。

函数原型：__aicore__ inline void SetAtomicMax<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；取最大值满足结合律，不存在非确定性问题。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMax](../../c_api/simd_atomic/asc_set_atomic_max.md)（`related`）：SetAtomicMax 与《AscSetAtomicMax》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [AscSetAtomicNone](../../c_api/simd_atomic/asc_set_atomic_none.md)（`related`）：SetAtomicMax 与《AscSetAtomicNone》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：SetAtomicMax 开启随路取大，DisableDmaAtomic 结束该状态，否则后续 DataCopy 会继续原子合并。
- [AscAtomicMax](../../c_api/scalar_compute/asc_atomic_max.md)（`same_topic`）：AscAtomicMax 与《SetAtomicMax》的衔接是：AscAtomicMax 是原子最大值更新；SIMT/basic AtomicMax 提供同一竞争更新语义，SetAtomicMax/AscSetAtomicMax 则配置后续搬运执行该原子操作。
- [AtomicMax](atomic_max.md)（`same_topic`）：SetAtomicMax 与《AtomicMax》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [SetAtomicMin](set_atomic_min_isasi.md)（`same_topic`）：SetAtomicMax 与《SetAtomicMin》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [SetAtomicType](set_atomic_type.md)（`same_topic`）：SetAtomicMax 对应 SetAtomicType 可选的 MAX 模式，补充专用接口及其数据类型边界。
- [asc_set_atomic_max_int（废弃）](../../c_api/simd_atomic/asc_set_atomic_max_int_deprecated.md)（`same_topic`）：asc_set_atomic_max_int（废弃） 的核心契约是“该接口已废弃，请使用asc_set_atomic_max_int32替代。 头文件路径："c_api/atomic/atomic.h"。 设置计算结果以原子比较的方式传输到GM。在拷贝前，将待传输的int32_t数据与GM中已有数据进行逐元素比较，并将最大值写入GM”；SetAtomicMax 补充“对后续搬运到GM的数据开启原子取大，将拷贝内容与GM已有值比较后写入最大值”。
<!-- cannbot:related:end -->
