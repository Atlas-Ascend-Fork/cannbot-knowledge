---
type: Guide
title: 设置合适的核数和算子Kernel类型
description: 在算子执行过程中，可能会因为以下几个原因产生额外的启动开销或者头开销：
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 设置合适的核数和算子Kernel类型

在算子执行过程中，可能会因为以下几个原因产生额外的启动开销或者头开销：

1.  **核启动**：每个核在启动时需要进行初始化操作，加载必要的配置和资源。
2.  **核取址TLB MISS**：当核在访问内存时，如果Translation Lookaside Buffer（TLB）中没有对应的页表项，就需要从内存中加载页表项，这会导致额外的延迟。
3.  **同地址访问冲突**：由于硬件限制，多个核同时访问相同的内存地址时可能会发生冲突，导致额外的时延。
4.  **变量资源初始化**：在算子执行前，需要初始化一些变量和资源，这也可能带来额外的性能开销。

头开销会随着使用的核数增加而增加。下图展示了这部分头开销随启动核数的变化情况。

**图1**  头开销随启动核数的变化

**对于整体耗时在微秒级别且单核计算量耗时较少的算子，可以通过减少启动核数并增加单核计算量的方式来获得性能提升。**这种优化方式的本质是在头开销耗时和单核计算量耗时之间进行权衡。为了达到最佳性能，开发者需要通过实践尝试，找到最合适的核数设置。

-   对于自定义算子工程，可以在TilingFunc（算子工程提供的在Host侧计算Tiling的默认函数）中通过SetSimdNumBlocks接口来设置算子使用的核数，具体设置方法请参考SetSimdNumBlocks；对于Kernel直调工程，可以在<<<>>>调用时指定算子使用的核数。
-   此外，算子的Kernel类型也会影响算子启动的核数。以纯Vector算子为例，如果以混合启动的方式执行该算子，调度器会同时启动Vector核和Cube核。然而，此时Cube核并没有实际的计算指令，但仍会产生核启动和核初始化的头开销。因此，建议设置合适的Kernel类型以最小化头开销。

    通常，算子工程会通过算子使用的指令自动识别算子类型，但该功能无法区分AIC和AIV的配比，默认按照AIV:AIC为1:2的配比下发任务。此外，自动识别功能可能失效，因为其依赖于编译优化的结果。所以推荐用户手动设置算子的Kernel类型。具体设置方法请参考设置Kernel类型。

<!-- cannbot:related:start -->
## 相关

- [SK_BIND（SuperKernel）](../../../../apis/utils_api/super_kernel/sk_bind.md)（`explains`）：设置合适的核数和算子Kernel类型 与《SK_BIND（SuperKernel）》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [SetKernelMode](../../../../apis/simd_api/basic_api/debug_interface/cpu_twin_debug/set_kernel_mode.md)（`explains`）：设置合适的核数和算子Kernel类型 与《SetKernelMode》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [设置Kernel类型](../../../../apis/simd_api/basic_api/kernel_tiling/set_kernel_type.md)（`explains`）：设置Kernel类型：SetKernelType的目标是只启动需要的 AIC/AIV核；优化指南解释选型，kernel_type runbook证明裸字段赋值无效，GetCoreNumAic/Vector提供合法核数输入。 目标卡《设置合适的核数和算子Kernel类型》补充：在算子执行过程中，可能会因为以下几个原因产生额外的启动开销或者头开销：
- [SIMD算子优化概述](../memory_access/avoid_ub_bank_conflict/overview.md)（`related`）：设置合适的核数和算子Kernel类型 与《SIMD算子优化概述》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [优化建议总览表（SIMD算子优化）](../optimization_summary.md)（`related`）：设置合适的核数和算子Kernel类型 与《优化建议总览表（SIMD算子优化）》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [直调 kernel-type 裸赋值标记无效](../../../../runbooks/compilation/kernel_type.md)（`related`）：设置合适的核数和算子Kernel类型 与《直调 kernel-type 裸赋值标记无效》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [核函数内删除Workspace相关冗余操作](remove_workspace_redundancy.md)（`same_topic`）：设置合适的核数和算子Kernel类型 与《核函数内删除Workspace相关冗余操作》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [核间负载均衡](../tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《设置合适的核数和算子Kernel类型》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
