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

- [稀疏反卷积精度误差源隔离配方](../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：“asc_atomic_add(outFeaturesGmPtr + gmOffset, partialOutPtr［ubOffset］);”展示 ScatterAdd 的实际原子累加；“原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。对于浮点累加顺序敏感场景，结果可能随线程调度变化而不同。”给出为何 SIMT 线程退化测试能隔离 FP32 顺序误差的接口边界。
- [原子操作指令优化](../../../guides/operator_practice/simt_operator_optimization/instruction_optimization/atomic_instruction_optimization.md)（`explains`）：“- asc_atomic_add接口性能对比样例：包含16个场景、归为5组对照实验，量化内存层级、原子累加组织方式、是否使用返回值、同一地址上的竞争程度与目标地址的Sector分布对原子加性能的影响。每组对照仅改变一个属性，其余配置保持一致。”与“对Unified Buffer或Global Memory中的数据与指定数据执行原子加操作，即将指定数据累加到这些内存区域的数据中。”。优化指南围绕 asc_atomic_add 的内存层级、返回值和竞争做对照，API 卡提供原子加合同。
<!-- cannbot:related:end -->
