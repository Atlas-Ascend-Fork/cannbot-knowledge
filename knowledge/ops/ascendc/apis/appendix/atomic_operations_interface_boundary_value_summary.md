---
type: API
title: 原子操作边界值汇总（附录）
description: 本节汇总介绍了原子操作接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/atomic_operations_interface_boundary_value_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 原子操作边界值汇总（附录）

本节汇总介绍了原子操作接口在边界值输入下的两类输出结果，以下内容针对如下型号生效：

涵盖以下类别：概述、原子操作接口边界值输入下的具体计算结果。

适用：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。

<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：焦点处理原子操作在边界输入下的结果解释；原子操作（AI Core SIMT编程）正文说明“SIMT编程模型中，一个Grid由多个Thread Block组成，每个Thread Block又包含多个Thread。不同Thread可以并发访问同一段Global Memory或Unified Buffer。当多个线程同时对同一地址执行读-改-写操作时，如果没有同步保护，可能”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
- [原子操作](../simd_api/basic_api/atomic_operations/atomic_operations.md)（`related`）：原子操作 与《原子操作边界值汇总（附录）》的实质衔接是：原子操作总览与 CAS/Add/Exch/Min/Max 和 store atomic 配置共同界定并发更新选择。
- [原子操作](../simt_api/atomic_operations/atomic_operations.md)（`related`）：原子操作 与《原子操作边界值汇总（附录）》的实质衔接是：SIMT 原子操作卡定义 GM/UB 作用域、读改写原子性以及不提供执行顺序；SIMT 指南、边界值表和 SIMD 原子概述用于选择作用域并验证边界，而不是替代同步。
- [原子操作简介](../simt_api/atomic_operations/atomic_operations_intro.md)（`related`）：边界值汇总补充各原子接口在特殊输入下的返回和写回结果，用于构造正确性测试。
- [原子操作概述](../simd_api/basic_api/atomic_operations/atomic_operations_overview.md)（`same_topic`）：焦点处理原子操作在边界输入下的结果解释；原子操作概述正文说明“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM的数”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
- [原子操作概述（SIMD原子操作）](../simd_api/c_api/simd_atomic/atomic_operations_overview.md)（`same_topic`）：焦点处理原子操作在边界输入下的结果解释；原子操作概述（SIMD原子操作）正文说明“数据搬运随路原子操作接口用于对后续目的地址为GM的数据搬运指令开启原子操作，涉及的接口请参见表1。如下图1的左侧子图所示，未开启原子操作时，写入GM的数据搬运完成后，GM中原始数据将被新搬运数据完全覆盖。如图1右侧子图所示，当数据搬运随路原子操作接口被调用后，系统将为后续写入GM”。候选给出边界表所依赖的原子读改写或随路原子语义，能据此解释极值、NaN 和溢出结果。
<!-- cannbot:related:end -->
