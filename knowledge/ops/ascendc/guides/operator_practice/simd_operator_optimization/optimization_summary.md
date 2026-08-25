---
type: Guide
title: 优化建议总览表（SIMD算子优化）
description: 汇总 SIMD 算子的 Tiling、启动开销、流水编排、内存访问、矢量计算和矩阵计算优化建议。
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/optimization_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 优化建议总览表

SIMD算子性能优化建议汇总，按五大分类组织：Tiling策略（核间负载均衡）、头尾开销优化（设置合适的核数和Kernel类型、限制TilingData大小、避免TPipe在对象内创建、删除Workspace冗余操作、设置DCI编译选项）、流水编排（开启DoubleBuffer、启用Iterate异步接口避免AIC/AIV同步）、内存访问（大数据块搬运、GM地址512B对齐、高效搬运API、避免同地址访问、L2 CacheMode配置、Buffer共享复用、避免UB bank冲突）、矢量计算与矩阵计算优化（UB融合、Counter模式、Mask复用、低延迟指令、BT Buffer bias计算、FP Buffer量化等）。

<!-- cannbot:related:start -->
## 相关

- [中级性能优化](../typical_operator_cases/simd_operator_impl/add_vector_operator/intermediate_optimization.md)（`related`）：中级性能优化 与《优化建议总览表（SIMD算子优化）》的实质衔接是：Add 中级优化围绕 mask 复用、双发、循环/融合与 Get/SetValue 访问开销实施。
- [指令双发优化](vector_compute/vf_optimization/dual_issue_optimization.md)（`related`）：指令双发优化 与《优化建议总览表（SIMD算子优化）》的实质衔接是：双发优化依赖 VF 融合、循环/掩码复用、原子与地址寄存器编排；这些卡分别提供发射冲突定位和可执行改写。
- [核函数内删除Workspace相关冗余操作](overhead_optimization/remove_workspace_redundancy.md)（`related`）：核函数内删除Workspace相关冗余操作 与《优化建议总览表（SIMD算子优化）》的实质衔接是：workspace 已直接是用户 Workspace 时不应再 SetSysWorkSpace/GetUserWorkspace；Workspace API、使用指南和 RESERVED/预偏移案例界定何时仍需系统区与局部区。
- [纯搬运类算子VECIN和VECOUT建议复用](memory_access/vecin_vecout_reuse.md)（`related`）：纯搬运类算子VECIN和VECOUT建议复用 与《优化建议总览表（SIMD算子优化）》的实质衔接是：VECIN/VECOUT 复用依赖 TQueBind 将输入输出逻辑位置绑定到同一物理队列；高效搬运、UB 融合和优化总览说明这种复用减少搬运与 UB 占用的适用边界。
- [设置合适的核数和算子Kernel类型](overhead_optimization/core_count_kernel_type.md)（`related`）：设置合适的核数和算子Kernel类型 与《优化建议总览表（SIMD算子优化）》的实质衔接是：核数、kernel 类型和 workspace 都会影响启动/头尾开销；SetKernelMode、负载均衡与 SK_BIND 卡给出 host 配置和核侧绑定的执行落点。
- [核间负载均衡](tiling_strategy/inter_core_load_balance.md)（`same_topic`）：核间负载均衡 与《优化建议总览表（SIMD算子优化）》的实质衔接是：核间负载均衡通过调整拖尾核与 block 数减少尾部空闲，并与核间同步、DoubleBuffer/异步 Iterate 和具体 Matmul/Philox 分块约束共同决定并行度。
<!-- cannbot:related:end -->
