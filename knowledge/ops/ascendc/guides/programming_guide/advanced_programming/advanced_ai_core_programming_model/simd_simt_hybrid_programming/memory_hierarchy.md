---
type: Guide
title: 内存层级（SIMD与SIMT混合编程）
description: 在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量最小，访问效率最高。
tags: [task.lookup, topic.programming_model.development_mode.hybrid_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 内存层级

## 整体内存资源
在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量最小，访问效率最高。
在混合编程场景下，UB内存是SIMT VF和SIMD VF的共享内存。Vector Function切换时，UB上的数据不会被清除，因此可通过UB实现Vector Function间的通信。下文UB划分章节详细说明UB如何划分为静态内存、动态内存、Data Cache等区域；数据通路章节介绍混合编程场景下的整体数据通路，并说明并行流水间的数据同步和访问GM时的缓存一致性问题。
## UB划分
UB内存空间总大小为256KB。UB按功能划分为四个主要区域，从低地址到高地址依次为静态内存、动态内存、预留空间和Data Cache，如下图所示。
### 内存空间说明
1.  静态内存：从内存的起始地址分配一段指定大小的内存空间，其大小在编译时确定，不可动态修改。
2.  动态内存：位于静态内存之后，其大小由>>中的dyn_ub_size参数指定，可通过以下方式申请使用。
-   使用动态数组分配。
-   通过LocalMemAllocator的Alloc接口申请。
由于动态内存均从静态内存结束位置之后开始分配，因此只能选择其中一种方式申请动态内存，否则可能导致地址空间重叠，从而引发未定义行为。
3.  预留空间：编译器和Ascend C的预留空间，大小固定为8KB。
4.  Data Cache：SIMT专有的Data Cache空间，可分配的内存大小范围为32KB到128KB，具体计算公式如下：
Data Cache作为访问GM内存的缓存，其大小会影响算子的访存效率。若Data Cache小于32KB，执行时会出现校验报错并退出，因此申请内存时需确保预留足够的Data Cache空间。
由于Data Cache、预留空间与用户申请的UB内存共用同一块UB，因此开发者无法使用全部UB空间，应确保SIMT和SIMD各个执行空间中的实际UB访问范围都不超过已申请的静态内存和动态内存大小。
静态内存和动态内存的声明或配置限定了用户使用UB内存的有效范围。若用户配置的内存大小不足，甚至未申请内存即直接访问UB地址，访问地址可能越过用户动、静态内存边界并落入Data Cache区域。由于Data Cache容量由UB总量扣除静态内存、动态内存和预留空间后确定，所以用户共享内存配置偏小会扩大可分配给Data Cache的剩余空间。当程序执行越过已申请的动、静态内存边界，发生越界写入行为时，未必立即表现为内存分配失败，但可能破坏SIMT全局内存访问的数据缓存，导致计算结果不稳定或算子精度异常。
混合编程模式下，可在SIMT VF、SIMD VF和MainScalar执行空间申请静态内存和动态内存。MainScalar是指Device侧在VF函数外部的执行空间。下图为不同执行空间申请内存时对应的UB内存排布示意图。
