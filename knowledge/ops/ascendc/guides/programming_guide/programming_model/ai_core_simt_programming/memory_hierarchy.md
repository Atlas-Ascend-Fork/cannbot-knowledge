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
