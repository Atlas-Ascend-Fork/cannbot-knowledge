---
type: API
title: SetAtomicMin
description: 对后续搬运到GM的数据开启原子取小，将拷贝内容与GM已有值比较后写入最小值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicMin_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicMin

设置DMA搬运时的随路原子操作为取最小值。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子取最小值（旧值和新值中的最小值）。

函数原型：__aicore__ inline void SetAtomicMin<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；取最小值满足结合律，不存在非确定性问题。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [AscSetAtomicMin](../../c_api/simd_atomic/asc_set_atomic_min.md)（`related`）：AscSetAtomicMin 与《SetAtomicMin》的实质衔接是：AscSetAtomicMin 开启后续搬出取小，并需用 None 复位；SetAtomicMin/AtomicMin 和 store atomic 配置给出同一原子写回状态机。
- [AtomicMin](atomic_min.md)（`related`）：SetAtomicMin 控制后续 DMA 搬出，AtomicMin 则立即对地址执行标量原子最小；两者用于按数据通路选型。
- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：SetAtomicMin 开启随路取小，DisableDmaAtomic 将后续 UB/L0C/L1→GM 恢复为覆盖写。
- [asc_atomic_min](../../../simt_api/atomic_operations/asc_atomic_min.md)（`related`）：asc_atomic_min 与《SetAtomicMin》的实质衔接是：SIMT、C scalar 与基础 API AtomicMin 操作同一原子最小值；AtomicMax 和 SetAtomicMin 给出相反操作与 Store 配置路径。
- [SetAtomicMax](set_atomic_max_isasi.md)（`same_topic`）：SetAtomicMax 与《SetAtomicMin》的实质衔接是：SetAtomicMax 与 C API 配置、AtomicMax 消费、SetAtomicMin 对照及状态清理构成同一随路原子配置生命周期。
- [SetAtomicType](set_atomic_type.md)（`same_topic`）：SetAtomicMin 对应 SetAtomicType 可选的 MIN 模式，补充专用接口及其数据类型边界。
<!-- cannbot:related:end -->
