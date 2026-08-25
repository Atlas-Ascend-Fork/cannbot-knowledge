---
type: Guide
title: 2201到3510架构变更
description: NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# 2201到3510架构变更

NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
-   新增多条数据通路。
-   AI Core核数增加。
-   UB容量提升。
-   新增SSBuffer核内存储单元，支持AIC核和AIV核通过Scalar访问。
-   SIMD编程基础上，支持SIMT编程、SIMD与SIMT混合编程。
-   AIV核采用Regbase架构，与NPU架构版本2201的Membase架构相比，可以直接对芯片的Vector寄存器Register进行操作，实现更大的灵活性和更好的性能。
具体来说，3510架构的主要变更如下各表所示。除此之外，3510架构还扩展了支持的数据类型，具体可参考数据类型介绍。
- 搬运单元
搬运单元变更
3510变更：产生的影响：影响的API接口
删除L1 Buffer到GM的数据通路。：现有接口不支持从L1 Buffer直接搬运数据到GM。开发者需要在L1 Buffer分配一块空间存放单位矩阵，利用MMAD矩阵乘法计算输出到L0C Buffer，从L0C Buffer通过Fixpipe（L0C到GM数据搬运）将数据搬运到GM。：DataCopy/DumpTensor
删除GM到L0A Buffer、L0B Buffer的数据通路。：原GM到L0A Buffer和L0B Buffer的数据搬运需要拆分为两步，即从GM到L1 Buffer的数据搬运和从L1 Buffer到L0A Buffer、L0B Buffer的数据搬运。：LoadData
新增UB到L1 Buffer的数据通路。：支持将数据直接从UB搬运到L1 Buffer，而无需先从UB搬运到GM，再从GM搬运到L1 Buffer，使用方式具体可参考DataCopy（UBToL1连续数据搬运）。：DataCopy
新增ND-DMA指令。：扩展DataCopy数据搬运接口的能力，相比基础数据搬运接口，可更加自由地配置搬入数据的维度信息及Stride，使用方式具体可参考DataCopy（GMToUB多维数据搬运NDDMA）。：DataCopy
新增L0C Buffer到UB的单向数据通路。：支持将数据直接从L0C Buffer搬运到UB，而无需先从L0C Buffer搬运到GM，再从GM搬运到UB，使用方式具体可参考Fixpipe（L0C到GM数据搬运）。：Fixpipe
扩展LoadData搬运指令。：新增支持MicroScaling（MX）场景的数据搬运，使用方式具体可参考LoadData。：LoadData
新增DN分型、L1Buffer->L0A Buffer不再支持transpose。：使用新特性具体可参考LoadDataWithTranspose。：LoadDataWithTranspose
Fixpipe新增NZ2DN随路转换（实现NZ到DN数据格式的随路变换）。

<!-- cannbot:related:start -->
## 相关

- [asc_copy_l12l0a](../../../apis/simd_api/c_api/cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a_arch_3510.md)（`explains`）：asc_copy_l12l0a 与《2201到3510架构变更》的实质衔接是：该 3510 接口把 512B L1 矩阵搬到 L0A；架构变体、转置/MX 入口及 GM→L1 上游构成实际 Cube 搬运链，迁移卡限定不同架构可用路径。
- [Ascend C API兼容性策略](../ascend_c_api_compatibility.md)（`related`）：架构变化解释兼容表中接口变化/不支持的硬件原因。
- [CMake arch 子目录隔离 dav-3510 专属 API](../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《2201到3510架构变更》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [基础API迁移指导](2201_to_3510_guide/basic_api_migration.md)（`related`）：架构变更卡列出删除/新增数据通路、Regbase 和 Subnormal 差异；基础 API 迁移卡把这些变化落实为 DataCopy、LoadData、SetLoadDataBoundary 等替代方案。
- [算子编译迁移指导](2201_to_3510_guide/op_compilation_migration.md)（`related`）：2201→3510 不仅改变 kernel API，还要求编译命令/CMake 的 --npu-arch 或工程 ASCEND_COMPUTE_UNIT/AddConfig 同步更新；目标卡补齐制品构建链。
- [避免bank冲突（NPU架构版本2201）](../../operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《2201到3510架构变更》补充：NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：
- [高阶API迁移指导](2201_to_3510_guide/advanced_api_migration.md)（`related`）：架构变化页解释为何某些 2201 高阶 API 在 3510 上签名、临时空间或能力发生变化。
- [NPU架构版本2201](../../programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md)（`same_topic`）：2201到3510架构变更说明NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：。
- [NPU架构版本3510](../../programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_3510.md)（`same_topic`）：架构卡列出 3510 的 AIC/AIV、Regbase 与新增/删除数据通路，迁移卡逐项说明这些变化对 DataCopy、LoadData、Fixpipe 等 API 的影响，是同一 3510 架构对象的实现与迁移切面。
- [跨代迁移指南概述](../overview.md)（`same_topic`）：跨代迁移指南概述 与《2201到3510架构变更》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
<!-- cannbot:related:end -->
