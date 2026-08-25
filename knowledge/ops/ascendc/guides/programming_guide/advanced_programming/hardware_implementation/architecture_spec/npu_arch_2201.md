---
type: Guide
title: NPU架构版本2201
description: 本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
tags: [task.lookup, topic.programming_model.execution_unit]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/hardware_implementation/architecture_spec/npu_arch_2201.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# NPU架构版本2201

本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
-   Atlas A3 训练系列产品/Atlas A3 推理系列产品
-   Atlas A2 训练系列产品/Atlas A2 推理系列产品
## 硬件架构图
如下图所示，本架构中AI Core分为AIC和AIV两个独立的核，分别用于矩阵计算和向量计算。AIC核与AIV核配比为1：2。每个核都有自己的Scalar单元，能独立加载自己的代码段。AIV与AIC之间通过Global Memory进行数据传递。
## 计算单元
Cube计算单元和Vector计算单元分离部署
本架构中，Cube计算单元和Vector计算单元分别部署在AIC核和AIV核上，每个核都有自己的Scalar单元，能独立加载自己的代码段。
Vector计算单元
-   Vector计算单元的数据来自于Unified Buffer，要求32字节对齐。
Cube计算单元
-   Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和中间结果。
## 存储单元
获取存储单元的内存空间大小
开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。

<!-- cannbot:related:start -->
## 相关

- [GetCurNpuArch](../../../../../apis/utils_api/platform_info/platform_ascend_c/get_cur_npu_arch.md)（`explains`）：GetCurNpuArch说明获取当前硬件平台芯片架构版本号。
- [Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa](../../../../../runbooks/compilation/arch_variant_lookup_chain_soc_ini_npuarch_dispatcher.md)（`related`）：Ascend arch 变体查证链路 SoC→ini→NpuArch→dispa说明从芯片型号经 platform_config ini 的 NpuArch/AIC_version 到 dispatcher 头文件的 __NPU_ARCH__ 分支，确定编译期命中的 dav_c* 变体文件，避免误读宏隔离的 C 头文件。
- [CMake arch 子目录隔离 dav-3510 专属 API](../../../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《NPU架构版本2201》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [arch35 kernel 上板报 507035 实为 arch 不匹配](../../../../../runbooks/compilation/arch35_kernel_507035_arch.md)（`related`）：arch35 kernel 上板报 507035 实为 arch 不匹配说明编译通过的 ascend950（arch35）SIMT kernel 在 Ascend910_93（arch22）板上运行 L0 用例 20/22 失败、报 ACL_ERROR_RT_VECTOR_CORE_EXCEPTION（507035）；判别方法为先核对 build --soc 与 npu-smi 硬件 arch，再怀疑 kernel 逻辑。该路线在 arch22 板上 banned，只能改路线。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../../../runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav说明CMakeLists.txt 的 ASC 编译选项 --npu-arch 必须传小写带连字符的 NpuArch 规范名 dav-2201，传 SoC 名 DAV2201 或全大写会被 bisheng 以 "Unsupported NPU architecture" 拒绝。
- [基本架构（硬件实现）](../basic_architecture.md)（`related`）：2201 规格给出基础架构在 A2/A3 类芯片上的具体核数、存储和流水参数。
- [基础API迁移指导](../../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/basic_api_migration.md)（`related`）：基础API迁移指导 与《NPU架构版本2201》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [避免bank冲突（NPU架构版本2201）](../../../../operator_practice/simd_operator_optimization/memory_access/avoid_ub_bank_conflict/avoid_bank_conflict_npu_arch_2201.md)（`related`）：避免bank冲突（NPU架构版本2201）：2201与3510卡解释不同 UB bank组织，2201架构约束给出硬件前提；同地址访问是正文读写冲突的直接特例，迁移卡说明跨代调整边界。 目标卡《NPU架构版本2201》补充：本节介绍__NPU_ARCH__版本号为2201的硬件架构和其功能说明。对应的产品型号为：
- [2201到3510架构变更](../../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_arch_changes.md)（`same_topic`）：2201到3510架构变更说明NPU架构版本3510的架构图如图1所示，总体来看，3510架构新增了以下特性：。
- [Ascend C API兼容性策略](../../../../cross_gen_migration_guide/ascend_c_api_compatibility.md)（`same_topic`）：Ascend C API兼容性策略说明本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。
<!-- cannbot:related:end -->
