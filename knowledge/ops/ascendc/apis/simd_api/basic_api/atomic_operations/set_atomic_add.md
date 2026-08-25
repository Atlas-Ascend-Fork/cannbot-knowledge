---
type: API
title: SetAtomicAdd
description: 对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/SetAtomicAdd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# SetAtomicAdd

设置DMA搬运时的随路原子操作为累加。调用后，后续从UB/L0C/L1到GM的DataCopy搬运将对目标GM地址执行原子累加（旧值+新值）。

函数原型：__aicore__ inline void SetAtomicAdd<T>()。模板参数T指定数据类型。参数：无。约束：与DisableDmaAtomic配合使用；浮点数累加可能产生非确定性结果。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/matmul_atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“SetAtomicAdd”定义：对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [AtomicAdd](atomic_add.md)（`related`）：SetAtomicAdd 配置后续 DataCopy 的原子累加，而 AtomicAdd 直接对一个 GM 地址执行读改写；二者的差异决定按标量更新还是搬运累加选型。
- [DisableDmaAtomic](disable_dma_atomic.md)（`related`）：SetAtomicAdd 开启后续搬出随路原子加，DisableDmaAtomic 用于在该段结束后恢复普通覆盖写；两者须成对界定作用域。
- [原子操作概述](atomic_operations_overview.md)（`related`）：概述中的 DMA 原子加需先 SetAtomicAdd 再搬出，并在结束后恢复状态；该页落实这一状态机。
- [AscAtomicAdd](../../c_api/scalar_compute/asc_atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《SetAtomicAdd》补充：对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。
- [AscSetAtomicAdd](../../c_api/simd_atomic/asc_set_atomic_add.md)（`same_topic`）：AscSetAtomicAdd 与 Basic API SetAtomicAdd 都配置后续 GM 搬运的原子加模式，是同一随路原子状态在 C/C++ 接口层的对应入口。
- [SetAtomicType](set_atomic_type.md)（`same_topic`）：SetAtomicAdd 是 SetAtomicType 的加法专用配置入口，二者控制同一 DMA 写 GM 原子状态。
<!-- cannbot:related:end -->
