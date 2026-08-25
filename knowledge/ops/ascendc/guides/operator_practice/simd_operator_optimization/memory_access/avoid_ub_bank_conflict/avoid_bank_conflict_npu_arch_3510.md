---
type: Guide
title: 避免bank冲突（NPU架构版本3510）
description: '>该性能优化建议适用于如下产品型号：'
tags: [task.lookup, topic.performance.optimization.optimization_overview]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_3510.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# 避免bank冲突（NPU架构版本3510）

【优先级】中
Unified Buffer缓存总大小为256KB，包含8个bank group，每个bank group包含2个bank。每个bank大小为16KB，由512行组成，每行长度为32B，采用低位地址交织。
UB的地址编码格式：
3510架构使用低位编址，地址排布情况如图所示：
每个bank可分为4个subbank，每个subbank宽度为8B，subbank仅在gather/scatter场景被感知，连续读写只感知到bank。
## bank冲突的典型场景
每个bank一拍只能完成一读或者一写，每个bank group最多只允许2读0写或者1读1写。根据内存结构，bank冲突主要可以分为以下三种类型：
-   读写冲突：读操作和写操作同时尝试访问同一个bank，或者两个读操作和一个写操作同时尝试访问同一个bank group。
-   写写冲突：多个写操作同时尝试访问同一个bank group。
-   读读冲突：两个读操作同时尝试访问同一个bank，或者两个以上读操作同时尝试访问同一个bank group。
注：bank冲突的场景与Unified Buffer的规格密切相关，规格的变化通常会导致bank冲突场景的变化。
### 基于连续访存的bank冲突分析
以下对连续访存的冲突类型进行解读：
-   读写冲突
同时读写到同一个bank时造成读写冲突，具体分析如下：
一读一写冲突示例
两读一写冲突示例
-   写写冲突
同时写入一个bank group造成写写冲突，具体分析如下：
写写冲突示例
-   读读冲突
读读冲突示例
### 基于离散访存的bank冲突分析
以下对离散访存下的冲突进行解读：
-   当gather/scatter访存数据分布在不同的subbank中时，不发生冲突。
-   当gather/scatter数据存在同一subbank的同一起始地址时，不发生冲突，因此相同索引值的访存不发生冲突。
-   当gather/scatter数据存在同一subbank的不同起始地址时，发生冲突。
-   gather/scatter会与连续访存指令/MTE搬运指令冲突。
## 如何避免bank冲突
避免bank冲突的方法如下：
- 通过地址重叠减少读指令
由于一个bank group最多支持两读或者一读一写，在两读一写时会因为读/写口不足而引发bank冲突，当读指令的起始地址重叠时，硬件会将指令优化为一条。
- 离散访存下，将数据分散到不同subbank
当gather/scatter数据存在同一subbank的不同起始地址时，发生冲突，可通过将数据分散到不同subbank来减少subbank冲突，避免不同起始地址的数据集中在同一subbank下。
- 优化计算逻辑
对一个数据类型为float，shape为(8, 64)的输入每个元素加1。通过将计算逻辑由逐列计算改为逐行计算可避免同一Repeat下的冲突问题，实现方案对比如下：

<!-- cannbot:related:start -->
## 相关

- [EnableL1BankConflictOptimise](../../../../../apis/simd_api/adv_api/cube_compute/matmul_tiling/enable_l1_bank_conflict_optimise.md)（`explains`）：EnableL1BankConflictOptimise 与《避免bank冲突（NPU架构版本3510）》的实质衔接是：该开关由 Matmul GetTiling 判定，随后写入 MatmulConfig 并通过新增 TilingKey 选择核侧分支；bank 规则和 key 位编码共同约束实现。
- [asc_copy_l12l0a](../../../../../apis/simd_api/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`explains`）：asc_copy_l12l0a 与《避免bank冲突（NPU架构版本3510）》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [SIMD算子优化概述](overview.md)（`related`）：概述解释 bank 结构与并发访问为何冲突，为 3510 卡中的具体 padding/地址排布方案提供机制基础。
- [避免UB的Bank冲突](../../../simt_operator_optimization/memory_access/avoid_ub_bank_conflict_simt.md)（`related`）：两张卡都处理 3510 UB bank 冲突；SIMT 卡强调线程/warp 访问，SIMD 卡给出 bank group、subbank 及连续/离散访存冲突模型，可互补定位同一硬件瓶颈。
- [避免bank冲突（NPU架构版本2201）](avoid_bank_conflict_npu_arch_2201.md)（`same_topic`）：2201 与 3510 文档针对同一 UB bank conflict 优化目标给出不同架构布局策略，对照可避免照搬地址间隔。
<!-- cannbot:related:end -->
