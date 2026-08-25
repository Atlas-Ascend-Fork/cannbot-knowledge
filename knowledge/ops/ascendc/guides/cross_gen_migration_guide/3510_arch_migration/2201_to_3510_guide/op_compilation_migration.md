---
type: Guide
title: 算子编译迁移指导
description: 进行算子编译时，开发者需要感知不同架构、不同的AI处理器型号。
tags: [task.lookup, topic.quality.compatibility.version_migration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 算子编译迁移指导

进行算子编译时，开发者需要感知不同架构、不同的AI处理器型号。
- 异构编译场景，开发者使用命令行或者编写Cmake文件进行编译的情况，需要手动修改NPU架构版本号或者AI处理器型号。以修改NPU架构版本号为例，更改编译命令行或编译工程CMakeLists.txt文件中的--npu-arch配置，示例如下：
- 对于使用msOpGen工具生成的标准自定义算子工程的情况，会自动在算子工程目录下生成编译配置项文件CMakePresets.json中，并自动填充ASCEND_COMPUTE_UNIT字段。开发者需要在进行算子原型定义时，通过AddConfig接口注册算子支持的AI处理器型号以及相关的配置信息。AddConfig接口原型如下：soc参数表示AI处理器型号，aicore_config表示其他配置信息。
通过该接口注册AI处理器型号的样例如下，ascendxxx填写规则请参考算子工程目录下编译配置项文件CMakePresets.json中的ASCEND_COMPUTE_UNIT字段，该字段取值在使用msOpGen创建工程时自动生成。

<!-- cannbot:related:start -->
## 相关

- [2201到3510架构变更](../2201_to_3510_arch_changes.md)（`related`）：2201→3510 不仅改变 kernel API，还要求编译命令/CMake 的 --npu-arch 或工程 ASCEND_COMPUTE_UNIT/AddConfig 同步更新；目标卡补齐制品构建链。
- [AI Core编译基本用法](../../../programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《算子编译迁移指导》具体提供“进行算子编译时，开发者需要感知不同架构、不同的AI处理器型号。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [Ascend C API兼容性策略](../../ascend_c_api_compatibility.md)（`related`）：接口兼容后仍需迁移编译配置和产物注册，构成工程下游步骤。
- [CMake arch 子目录隔离 dav-3510 专属 API](../../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《算子编译迁移指导》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [CMake函数参考（附录）](../../../programming_guide/advanced_programming/aclnn_operator_development/appendix/cmake_function_reference.md)（`related`）：CMake函数参考（附录） 与《算子编译迁移指导》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../../runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《算子编译迁移指导》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [基础API迁移指导](basic_api_migration.md)（`related`）：基础API迁移指导 与《算子编译迁移指导》的实质衔接是：基础 API 迁移与架构变化、兼容策略及编译/高阶迁移共同组成 2201 到 3510 的改造流程；所连具体卡验证被删除接口、硬件约束和替代调用。
- [高阶API迁移指导](advanced_api_migration.md)（`related`）：接口改完后还需按 3510 编译配置、产物和注册流程迁移，构成下游工程步骤。
- [跨代迁移指南概述](../../overview.md)（`same_topic`）：跨代迁移指南概述 与《算子编译迁移指导》的实质衔接是：迁移概述把兼容性判断、架构差异、基础/高阶 API 修改和算子编译迁移串成同一套 2201→3510 决策流程。
<!-- cannbot:related:end -->
