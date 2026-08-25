---
type: API
title: AscAtomicAdd
description: 对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicAdd

对Global Memory中的数据与指定数据执行原子加操作，即将val累加到address指向的数据元素上。 将address指向的GM地址上的旧值（old_value）与输入标量值（val）求和，将和结果（new_value）写回GM地址，返回该地址修改前的值（old_value）。
函数原型：int32_t asc_atomic_add(__gm__ int32_t *address, int32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_add为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [Matmul开启AtomicAdd选项](../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/matmul_atomic_add.md)（`explains`）：“Matmul开启AtomicAdd选项”定义：【描述】__对于Matmul得到的结果矩阵C\(m, n\)，若后续需要和GM上的矩阵D\(m, n\)进行Add操作，则可以在GetTensorC接口或者IterateAll接口的GM通路上，将enAtomic参数设为1，开启AtomicAdd累加操作，在搬出矩阵C到GM时，矩阵C的结果将直接累加到矩阵D的GM地址上，从而实现与矩阵D的Add操作。；“AscAtomicAdd”定义：对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。。实质衔接：Matmul GM 搬出可用 SetAtomicAdd/enAtomic 直接累加 D；L0C 暂存是避免 GM 往返的另一方案，标量原子接口用于区分普通地址原子与搬出原子模式。
- [原子操作指令优化](../../../../guides/operator_practice/simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`explains`）：《原子操作指令优化》处理“【描述】SIMT编程模式下，多个线程更新同一个内存地址时需要使用原子操作接口保证更新结果正确。原子操作属于高开销指令，其耗时由两方面决定：一是同一地址上的原子操作只能排队依次执行，二是单条原子指令的处理开销。”。《AscAtomicAdd》明确提供“对Global Memory中的数据执行原子加操作，将val累加到address指向的数据元素上，返回修改前的值。”，其参数、调用或验证步骤直接接入原子写优化的冲突模型、AtomicAdd/Inc 实现和性能验证。
- [AscAtomicSub](asc_atomic_sub.md)（`same_topic`）：AscAtomicSub 与《AscAtomicAdd》的实质衔接是：SIMT asc_atomic_sub 是同一 GM 原子减；原子加提供逆操作对照，绕过 DCache 的读写和 AscDcci 共同落实 focal 明示的缓存一致性要求。
- [AscSetAtomicAdd](../simd_atomic/asc_set_atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《AscSetAtomicAdd》补充：对后续目的地址为GM的数据搬运指令开启原子累加，将待搬运数据与GM已有数据求和后写入GM。
- [AtomicAdd](../../basic_api/atomic_operations/atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《AtomicAdd》补充：对GM地址上的值执行原子加操作，将旧值与输入标量求和后写回，返回修改前的旧值。
- [SetAtomicAdd](../../basic_api/atomic_operations/set_atomic_add.md)（`same_topic`）：AscAtomicAdd：AscAtomicAdd、SIMT asc_atomic_add 与基础 AtomicAdd执行同一 GM 原子累加；SetAtomicAdd/AscSetAtomicAdd则控制后续搬运累加，需避免混淆即时原子与搬运配置。 目标卡《SetAtomicAdd》补充：对后续搬运到GM的数据开启原子累加，将拷贝内容与GM已有值求和后写入。
- [asc_atomic_add](../../../simt_api/atomic_operations/asc_atomic_add.md)（`same_topic`）：SIMD 标量 AscAtomicAdd 与 SIMT asc_atomic_add 都对目标地址做原子读改加并返回旧值；SIMT 版本还支持 UB，而 SIMD 标量卡限定 GM。
<!-- cannbot:related:end -->
