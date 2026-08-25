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

- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：DisableDmaAtomic 负责结束 SetAtomicType 建立的 DMA 原子状态，避免后续搬运错误继承原子语义。
- [GetStoreAtomicConfig](get_store_atomic_config_isasi.md)（`related`）：GetStoreAtomicConfig 可读取当前搬出原子配置，用于验证 SetAtomicType 后的模式及排查残留状态。
- [关键特性说明（原子操作）](key_features.md)（`related`）：SetAtomicType 用于按关键特性页选择 add/max/min 等原子类型，决定是否存在浮点加法非结合风险。
- [SetAtomicAdd](set_atomic_add.md)（`same_topic`）：SetAtomicAdd 是 SetAtomicType 的加法专用配置入口，二者控制同一 DMA 写 GM 原子状态。
- [SetAtomicMax](set_atomic_max_isasi.md)（`same_topic`）：SetAtomicMax 对应 SetAtomicType 可选的 MAX 模式，补充专用接口及其数据类型边界。
- [SetAtomicMin](set_atomic_min_isasi.md)（`same_topic`）：SetAtomicMin 对应 SetAtomicType 可选的 MIN 模式，补充专用接口及其数据类型边界。
<!-- cannbot:related:end -->
