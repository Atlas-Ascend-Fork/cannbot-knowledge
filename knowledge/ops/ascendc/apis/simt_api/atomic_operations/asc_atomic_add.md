---
type: API
title: asc_atomic_add
description: 对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_add.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950']
---

# asc_atomic_add

对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。
函数原型：int32_t asc_atomic_add(int32_t *address, int32_t val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于浮点累加顺序敏感场景，结果可能随线程调度变化而不同。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。具体性能对比和优化示例请参见asc_atomic_add接口性能对比样例。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half、bfloat16_t、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [原子操作指令优化](../../../guides/operator_practice/simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`explains`）：《原子操作指令优化》处理“【描述】SIMT编程模式下，多个线程更新同一个内存地址时需要使用原子操作接口保证更新结果正确。原子操作属于高开销指令，其耗时由两方面决定：一是同一地址上的原子操作只能排队依次执行，二是单条原子指令的处理开销。”。《asc_atomic_add》明确提供“对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。”，其参数、调用或验证步骤直接接入原子写优化的冲突模型、AtomicAdd/Inc 实现和性能验证。
- [AtomicAdd](../../simd_api/basic_api/atomic_operations/atomic_add.md)（`related`）：基础 AtomicAdd 提供相同 GM 原子读改写/返回旧值语义，是 C++ 基础 API 的直接映射。
- [asc_atomic_sub](asc_atomic_sub.md)（`related`）：AscAtomicAdd 是同一 SIMT 地址与返回旧值模型下的加法对偶，可据更新方向选择且共享并发顺序不确定性。
- [asc_set_store_atomic_config_v2（废弃）](../../simd_api/c_api/simd_atomic/asc_set_store_atomic_config_v2_deprecated.md)（`related`）：废弃卡明确要求原子加迁移到 asc_atomic_add；目标接口给出原子读改写、返回旧值、内存空间和浮点顺序敏感约束。
- [AscAtomicAdd](../../simd_api/c_api/scalar_compute/asc_atomic_add.md)（`same_topic`）：SIMD 标量 AscAtomicAdd 与 SIMT asc_atomic_add 都对目标地址做原子读改加并返回旧值；SIMT 版本还支持 UB，而 SIMD 标量卡限定 GM。
<!-- cannbot:related:end -->
