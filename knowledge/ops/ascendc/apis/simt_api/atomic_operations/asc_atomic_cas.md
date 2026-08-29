---
type: API
title: asc_atomic_cas
description: 对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
tags: [task.lookup, topic.implementation.atomic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_cas.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_atomic_cas

对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
函数原型：float asc_atomic_cas(float *address, float compare, float val)
返回值：Unified Buffer或Global Memory上的初始数据。
约束：原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。使用asc_atomic_cas实现抢占逻辑时，可保证最多一个线程抢占成功，但不保证固定由哪个线程抢占成功。；本接口的性能受以下因素影响，相关原理请参见原子操作机制。；内存空间：Unified Buffer的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持Unified Buffer（即int32_t、uint32_t、float、half2、bfloat16x2_t）时，建议优先在Unified Buffer中完成原子操作。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”；“原子操作不保证多个线程到达该原子操作的先后顺序，也不是线程同步屏障。”。指南解释 CAS 的并发语义和不提供线程顺序/屏障的边界，直接支撑接口的正确使用。
- [ScatterMax 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_max_950.md)（`related`）：“重复 `indices` 或并发命中同一元素时，CAS retry loop 把每次最大值更新串行化到该 GM 地址；固定源码没有给出重复索引的确定执行次序保证。”；“原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。”。CAS API 合同直接解释 ScatterMax 重复索引的同步保证与非确定顺序边界。
- [ScatterMin 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_min_950.md)（`related`）：“Kernel 对同一目标元素的并发更新使用 CAS 重试；越界 `indices［m］` 直接 `continue`。”与“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”提供双方正文证据。ScatterMin 以 CAS 重试保护同一目标元素的并发最小值更新，API 卡定义比较相等才写入并返回旧值的原子合同，解释了重试循环的正确性基础。
- [ScatterMul 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_mul_950.md)（`related`）：“更新是原地的，Kernel 的 `y` 参数不被读取或写入。重复索引通过 CAS 重试串行化相同目标元素的 read-modify-write；不同线程的成功次序不固定，因此浮点重复乘法的舍入次序也不固定。”与“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”提供双方正文证据。ScatterMul 卡明确用 CAS 重试实现重复索引下的原地乘法更新，asc_atomic_cas 卡定义比较成功才写入的原子原语；后者直接解释前者避免同地址更新丢失的机制。
- [AscAtomicCas](../../simd_api/c_api/scalar_compute/asc_atomic_cas.md)（`same_topic`）：对Global Memory中address指向的元素执行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。；对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。两卡定义同一 compare-and-swap 决策，分别给出 Scalar C API 的缓存同步合同与 SIMT 的线程竞争合同。
<!-- cannbot:related:end -->
