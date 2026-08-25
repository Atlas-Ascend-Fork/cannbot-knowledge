---
type: Guide
title: 避免bank冲突（NPU架构版本2201）
description: '>该性能优化建议适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# 避免bank冲突（NPU架构版本2201）

【优先级】高
【描述】为了提高数据访问的效率和吞吐量，Unified Buffer采用了bank（大小相等的内存模块）结构设计。Unified Buffer总大小为192K，划分为48个bank。每个bank由128行组成，每行长度为32B。这48个bank进一步组织为16个bank group，每个bank group包含3个bank，例如bank15、bank31和bank47组成一个bank group。
每个bank可以独立地进行数据的读写操作，允许多个数据请求同时进行。然而，当多个读写操作试图同时访问同一个bank或bank group时，由于硬件资源的限制，这些操作必须排队等待，会导致bank冲突，引起性能下降。
具体来说，Vector计算单元每拍（一个指令周期）能够从每个bank group中读取或写入一行数据。如果同一个API中的多个操作试图同时访问同一个bank或bank group，Vector计算单元无法在同一个周期内处理所有请求，导致这些请求排队等待。这种排队增加了数据访问的延迟，降低了系统的整体性能。
## bank冲突的典型场景
bank冲突主要可以分为以下三种场景：
-   读写冲突：读操作和写操作同时尝试访问同一个bank。
-   写写冲突：多个写操作同时尝试访问同一个bank group。
-   读读冲突：多个读操作同时尝试访问同一个bank group。
下文给出了一些具体的示例，假设，0x10000地址在bank16上，0x10020在bank17上，0x20020在bank33上，如下图所示：
-   读写冲突示例
Vector指令的源操作数src和目的操作数dst同时读写到同一个bank时造成读写冲突，具体分析如下：
读写冲突示例
-   写写冲突示例
Vector指令目的操作数dst对应的8个DataBlock（block0-block7）同时写到一个bank group时造成写写冲突，具体分析如下：
写写冲突示例
-   读读冲突
-   Vector指令多个源操作数同时读到同一个bank group时造成读读冲突，具体分析如下：
双src场景读读冲突示例
-   Vector指令某一个源操作数对应的8个DataBlock（block0-block7）读到同一个bank group时造成读读冲突，具体分析如下：
单src场景读读冲突示例
## 如何避免bank冲突
避免bank冲突的方法有两种：优化计算逻辑和优化地址分配。
-   优化计算逻辑
对一个shape为(8, 16, 16)的输入做(1, 0, 2)的transpose操作，输出shape为(16, 8, 16)。通过将计算逻辑由“跳读，连续写”修改为“连续读，跳写”可避免冲突问题。

<!-- cannbot:related:start -->
## 相关

- [EnableL1BankConflictOptimise](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_l1_bank_conflict_optimise.md)（`explains`）：EnableL1BankConflictOptimise 与《避免bank冲突（NPU架构版本2201）》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [Vector逻辑架构](../../../../../apis/simd_api/basic_api/memory_vector_compute/vector_logical_arch/vector_logical_arch.md)（`explains`）：Vector 逻辑架构中的 UB bank、矢量访问宽度和冲突机制是该指南调整地址错位以避开 bank 冲突的硬件依据。
- [2201到3510架构变更](../../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《2201到3510架构变更》补充：NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
- [NPU架构版本2201](../../../../programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《NPU架构版本2201》补充：本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
- [NPU架构版本2201](../../../../programming_guide/advanced_programming/hardware_implementation/hardware_constraints/npu_arch_2201.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《NPU架构版本2201》补充：本节介绍硬件约束以及解决方案建议。对应的产品型号为：
- [避免同地址访问](../avoid_same_address_access.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《避免同地址访问》补充：>该性能优化指导适用于如下产品型号：
- [避免bank冲突（NPU架构版本3510）](avoid_bank_conflict_npu_arch_3510.md)（`same_topic`）：2201 与 3510 文档针对同一 UB bank conflict 优化目标给出不同架构布局策略，对照可避免照搬地址间隔。
<!-- cannbot:related:end -->
