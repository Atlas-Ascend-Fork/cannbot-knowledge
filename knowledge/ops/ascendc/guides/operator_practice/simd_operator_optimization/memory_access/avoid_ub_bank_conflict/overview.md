---
type: Guide
title: SIMD算子优化概述
description: 为了提高数据访问的效率和吞吐量，Unified Buffer采用了大小相等的内存模块（bank）结构设计。当多条读写指令同时访问Unified
  Buffer时，由于硬件资源的限制，这些指令不能同时执行，从而引发bank冲突。在这种情况下，指令需要排队等待资源，无法在一个指令周期内完成。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 概述

【优先级】高

【概述】

为了提高数据访问的效率和吞吐量，Unified Buffer采用了大小相等的内存模块（bank）结构设计。当多条读写指令同时访问Unified Buffer时，由于硬件资源的限制，这些指令不能同时执行，从而引发bank冲突。在这种情况下，指令需要排队等待资源，无法在一个指令周期内完成。

-   针对NPU架构版本2201



    UB总大小为192KB，包含16个bank group，每个bank group包含3个bank。每个bank大小为4KB，由128行组成，每行长度为32B。

    -   **读写冲突**：读操作和写操作同时尝试访问同一个bank。
    -   **写写冲突**：多个写操作同时尝试访问同一个bank group。
    -   **读读冲突**：多个读操作同时尝试访问同一个bank group。

-   针对NPU架构版本3510



    UB总大小为256KB，包含8个bank group，每个bank group包含2个bank。每个bank大小为16KB，由512行组成，每行长度为32B。

    -   **读写冲突**：读操作和写操作同时尝试访问同一个bank。
    -   **写写冲突**：多个写操作同时尝试访问同一个bank group。
    -   **读读冲突**：两个读操作同时尝试访问同一个bank，或者两个以上读操作同时尝试访问同一个bank group。

可以看出bank冲突的场景与Unified Buffer的规格密切相关，规格的变化通常会导致bank冲突场景的变化。

-   由于NPU架构版本3510的bank group上有两组读口和写口，因此两次读操作访问同一个bank group的不同bank时，不会引起冲突。
-   假设读指令操作的地址为0x0000（bank0），写指令操作的地址为0x10000 ，在NPU架构版本2201中，地址0x10000（bank16）不会发生读写冲突，而在NPU架构版本3510中，这个地址0x10000（bank0）会引发读写冲突。

下文介绍不同硬件架构下如何避免bank冲突。

<!-- cannbot:related:start -->
## 相关

- [指令双发优化](../../vector_compute/vf_optimization/dual_issue_optimization.md)（`related`）：指令双发优化 与《SIMD算子优化概述》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [核函数内删除Workspace相关冗余操作](../../overhead_optimization/remove_workspace_redundancy.md)（`related`）：核函数内删除Workspace相关冗余操作 与《SIMD算子优化概述》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [设置合适的核数和算子Kernel类型](../../overhead_optimization/core_count_kernel_type.md)（`related`）：设置合适的核数和算子Kernel类型 与《SIMD算子优化概述》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [避免bank冲突（NPU架构版本3510）](avoid_bank_conflict_npu_arch_3510.md)（`related`）：概述解释 bank 结构与并发访问为何冲突，为 3510 卡中的具体 padding/地址排布方案提供机制基础。
- [核间负载均衡](../../tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《SIMD算子优化概述》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
