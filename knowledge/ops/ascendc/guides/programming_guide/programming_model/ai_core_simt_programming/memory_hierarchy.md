---
type: Guide
title: 内存层级（AI Core SIMT编程）
description: SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/memory_hierarchy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 内存层级

SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期。
内存类型：线程作用域：生命周期：物理位置
全局内存：Grid：应用程序：Device
共享内存：Block：核函数：Vector Core
栈空间：Thread：核函数：Global Memory
寄存器：Thread：核函数：Vector Core
-   全局内存是所有线程均可直接访问的内存资源，即Global Memory；
-   共享内存是线程块内所有线程共享的内存，位于Unified Buffer，生命周期和线程块一致。
-   每个线程拥有独立的栈空间，主要用于存放线程私有临时数据。
-   每个线程拥有独立的寄存器，用于存储局部变量。
-   在访问性能方面，寄存器具有最高的访问速度；共享内存的访问效率优于全局内存。
内存层级如下图所示：
## 全局内存（Global Memory）
Device侧的全局内存是整个Grid中所有线程均可访问的内存空间。全局内存具有持久性：通过全局内存分配的空间及其存储的数据将持续保留，直到该内存空间被释放或应用程序终止。用户需在核函数启动前通过Runtime API完成全局内存的分配与初始化，核函数执行期间SIMT每个线程均可读写全局内存，执行完毕后可将结果拷贝回Host。有关Runtime API的更多信息与细节，可以参考《Runtime运行时API》。
运行在Device侧的核函数可以通过指针直接访问全局内存。下述代码展示了全局内存的简易示例。数组x、y、z均存储于全局内存中，通过以下核函数实现每个线程对全局内存的访问和存储。
## 共享内存
共享内存是同一线程块内所有线程均可访问的内存空间，位于每个Vector Core（AIV）内的Unified Buffer。与全局内存相比，共享内存的容量较小，但具有更高的带宽和更低的访问延迟，可视为内核执行期间由用户管理的高速缓存资源。
用户可通过动态或者静态方式申请共享内存。
1.  静态申请：分配一段指定大小的内存空间，其大小在编译时确定，不可动态修改，开发者通过数组分配申请使用。
默认情况下，申请到的静态内存首地址按照数据类型对齐，也支持用户使用__align__(N)手动指定对齐。
2.  动态申请：用户需要通过>>中参数dyn_ubuf_size指定动态内存的空间大小，其大小在运行期确定，SIMT编程中可通过以下方式申请使用动态内存。
### 共享内存大小的限制
如下图所示，Unified Buffer内存空间总大小为256KB。默认编译模式下，UB按功能划分为四个主要区域，从低地址到高地址依次为静态内存、动态内存、预留空间和Data Cache。由于这四类区域共享同一块Unified Buffer内存，因此用户在配置共享内存大小时，应确保为Data Cache保留足够的空间（至少32KB），避免因可用空间不足导致校验报错。

<!-- cannbot:related:start -->
## 相关

- [SIMT编程简介](../../../../apis/simt_api/simt_programming_intro/simt_programming_intro.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；SIMT编程简介正文界定“SIMT编程简介，包含编程模型、扩展语法和API列表的导航入口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [内存栅栏接口](../../../../apis/simt_api/sync_and_memory_fence/memory_fence/memory_fence.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；内存栅栏接口正文界定“提供线程与块级别的内存栅栏接口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [内存空间限定符](../../../../apis/simt_api/simt_programming_intro/extended_syntax/memory_space_qualifier.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；内存空间限定符正文界定“在SIMT编程中使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定的，动态内存的大小在核函数启动时确定”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [同步与内存栅栏](../../../../apis/simt_api/sync_and_memory_fence/sync_and_memory_fence.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步与内存栅栏正文界定“同步与内存栅栏接口索引，包含同步接口与内存栅栏接口”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [同步与内存栅栏简介（同步与内存屏障）](../../../../apis/simt_api/sync_and_memory_fence/sync_and_memory_fence_intro.md)（`explains`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步与内存栅栏简介（同步与内存屏障）正文界定“SIMT程序中，不同Thread的执行进度和内存访问到达顺序可能不同。当线程之间存在数据依赖时，需要使用同步接口或内存栅栏接口约束执行顺序和内存可见性”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [原子操作（AI Core SIMT编程）](atomic_operations.md)（`related`）：原子接口可作用于 Global Memory 或 Unified Buffer；内存层级卡给出两者的线程作用域和生命周期，决定竞争范围。
- [异构系统（编程模型）](../heterogeneous_system.md)（`related`）：焦点处理SIMT 内存层级与地址空间、同步可见性；异构系统（编程模型）正文界定“一个基于昇腾处理器的异构系统通常包含CPU与昇腾NPU。其中，CPU及其内存称为Host与Host Memory；NPU及其内存称为Device与Device Memory”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [编程示例（AI Core SIMT编程）](programming_examples.md)（`related`）：内存层级（AI Core SIMT编程）说明SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
- [ThreadArchitecture](thread_architecture.md)（`same_topic`）：焦点处理SIMT 内存层级与地址空间、同步可见性；ThreadArchitecture正文界定“SIMT编程模型采用Grid、Thread Block、Thread分层线程组织结构，每个层次维度可自定义配置，通过Warp调度机制执行”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [内存层级（SIMD与SIMT混合编程）](../../advanced_programming/advanced_ai_core_programming_model/simd_simt_hybrid_programming/memory_hierarchy.md)（`same_topic`）：焦点处理SIMT 内存层级与地址空间、同步可见性；内存层级（SIMD与SIMT混合编程）正文界定“在SIMD与SIMT混合编程场景下，整体内存资源如下图所示。核外的Global Memory是所有核的全局内存，容量最大，但访问效率最低。AIC的L1和AIV的UB是单核内的共享内存，容量较小，但访问效率较高。私有内存层最靠近计算单元，容量”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [同步机制（AI Core SIMT编程）](synchronization.md)（`same_topic`）：焦点处理SIMT 内存层级与地址空间、同步可见性；同步机制（AI Core SIMT编程）正文界定“SIMT是一种单指令多线程的编程模型，该编程模型旨在通过多线程并发执行达到隐藏访存延迟，提升计算吞吐量的目的。SIMT编程模型中，一个Thread Block内的多个Thread并行执行，不同Thread的执行进度和内存访问到达顺序可能不同”。候选给出 SIMT 线程/硬件层级、地址空间限定符和 fence/sync 的可见性边界。
- [抽象硬件架构（AI Core SIMT编程）](abstract_hardware_architecture.md)（`same_topic`）：“抽象硬件架构（AI Core SIMT编程）”处理AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和复杂控制逻辑等场景。SIMT编程能够有效简化复杂…；“内存层级（AI Core SIMT编程）”明确SIMT线程可访问多种内存空间。下表汇总了SIMT编程中常见内存类型的作用域及其生命周期。。实质衔接：正文明确把 SIMT 抽象建立在线程层级和内存层级上，并指向底层 AI Core 架构；只连接理解资源分配所必需的章节。
<!-- cannbot:related:end -->
