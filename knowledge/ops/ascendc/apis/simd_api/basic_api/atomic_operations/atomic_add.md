---
type: API
title: AtomicAdd
description: 对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/atomic_operations/AtomicAdd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AtomicAdd

在指定GM地址上进行原子加操作。将address指向的GM地址上的旧值与输入值进行原子加运算，将结果写回GM地址，返回修改前的旧值。仅Ascend 950PR/950DT支持。

函数原型通过模板参数T指定数据类型（支持int32_t/uint32_t/int64_t/uint64_t/float等）。接口参数：address为GM地址指针；value为输入标量值。返回值为修改前的旧值。

约束：仅支持标量操作；遵循通用地址对齐约束。头文件：basic_api/kernel_operator_atomic_intf.h。

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/matmul_atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“AtomicAdd”定义：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [原子操作指令优化](../../../../guides/operator_practice/simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`explains`）：《原子操作指令优化》处理“【描述】SIMT编程模式下，多个线程更新同一个内存地址时需要使用原子操作接口保证更新结果正确。原子操作属于高开销指令，其耗时由两方面决定：一是同一地址上的原子操作只能排队依次执行，二是单条原子指令的处理开销。”。《AtomicAdd》明确提供“对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。”，其参数、调用或验证步骤直接接入原子写优化的冲突模型、AtomicAdd/Inc 实现和性能验证。
- [SetAtomicAdd](set_atomic_add.md)（`related`）：SetAtomicAdd 配置后续 DataCopy 的原子累加，而 AtomicAdd 直接对一个 GM 地址执行读改写；二者的差异决定按标量更新还是搬运累加选型。
- [asc_atomic_add](../../../simt_api/atomic_operations/asc_atomic_add.md)（`related`）：基础 AtomicAdd 提供相同 GM 原子读改写/返回旧值语义，是 C++ 基础 API 的直接映射。
- [原子操作概述](atomic_operations_overview.md)（`related`）：概述明确将标量地址原子加与 DMA 原子状态区分；AtomicAdd 是前者的具体即时读改写接口。
- [AscAtomicAdd](../../c_api/scalar_compute/asc_atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《AtomicAdd》补充：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
<!-- cannbot:related:end -->
