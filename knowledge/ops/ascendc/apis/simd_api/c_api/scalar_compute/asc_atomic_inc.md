---
type: API
title: AscAtomicInc
description: 对Global Memory中address指向的计数器执行原子递增操作，若值大于等于val则赋值为0，否则加1。
tags: [task.lookup, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/scalar_compute/asc_atomic_inc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# AscAtomicInc

对Global Memory中address指向的计数器执行原子递增操作，如果address上的数值大于等于指定数值val，则对address赋值为0，否则将address上数值加1。
函数原型：uint32_t asc_atomic_inc(__gm__ uint32_t *address, uint32_t val)
返回值：address地址中计算前的原始数据。
约束：在开启编译器自动同步功能的前提下，编译器能够自动在PIPE_MTE2/PIPE_MTE3与PIPE_S之间插入同步。但是，asc_atomic_inc为标量计算，在读写GM时如果与搬运单元（MTE2/MTE3）存在数据依赖，编译器却无法自动插入同步，开发者需要根据实际情况手动插入同步。；Scalar原子操作会绕过DCache，需要调用asc_dcci接口确保GM与DCache的一致性。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [原子操作指令优化](../../../../guides/operator_practice/simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`explains`）：《原子操作指令优化》处理“【描述】SIMT编程模式下，多个线程更新同一个内存地址时需要使用原子操作接口保证更新结果正确。原子操作属于高开销指令，其耗时由两方面决定：一是同一地址上的原子操作只能排队依次执行，二是单条原子指令的处理开销。”。《AscAtomicInc》明确提供“对Global Memory中address指向的计数器执行原子递增操作，若值大于等于val则赋值为0，否则加1。”，其参数、调用或验证步骤直接接入原子写优化的冲突模型、AtomicAdd/Inc 实现和性能验证。
- [AscAtomicDec](asc_atomic_dec.md)（`same_topic`）：AscAtomicDec：AscAtomicDec与SIMT asc_atomic_dec执行同一GM原子自减，AscAtomicInc提供相反更新的边界对照，便于验证返回值和上下界行为。 目标卡《AscAtomicInc》补充：对Global Memory中address指向的计数器执行原子递增操作，若值大于等于val则赋值为0，否则加1。
- [asc_atomic_inc](../../../simt_api/atomic_operations/asc_atomic_inc.md)（`same_topic`）：asc_atomic_inc说明对Unified Buffer或Global Memory上address的数值进行原子加1操作，如果address上的数值大于等于指定数值val，则对address赋值为0，否则将address上数值加1。
<!-- cannbot:related:end -->
