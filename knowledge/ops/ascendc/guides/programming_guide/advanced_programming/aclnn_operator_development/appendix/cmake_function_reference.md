---
type: Guide
title: CMake函数参考（附录）
description: 本文是参考内容，整理算子工程编译过程涉及的CMake函数接口，供需要深入了解编译机制的高级开发者查阅。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/appendix/cmake_function_reference.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# CMake函数参考

本文是参考内容，整理算子工程编译过程涉及的CMake函数接口，供需要深入了解编译机制的高级开发者查阅。
## 概述
使用msOpGen工具创建算子工程时，相关编译脚本被固化在本地。为便于开发者直接使用算子工程对外提供的cmake函数接口而无需频繁重建工程，CANN软件包中将算子工程的cmake脚本打包，开发者可通过find_package查找对应的cmake modules包来使用这些函数。
本文说明算子工程编译过程中使用的8个CMake函数，按用途分为Package类、Library类、其他三类。
## 函数一览
分类：函数：功能
Package：npu_op_package：创建一个package。
Package：npu_op_package_add：将目标或文件添加到package中。
Library：npu_op_library：创建Host侧库。
Library：npu_op_kernel_library：创建Kernel侧库。
Library：npu_op_kernel_options：添加Kernel目标编译选项。
Library：npu_op_kernel_sources：描述Kernel目标的源码信息。
Library：npu_op_device_tiling_library：创建Device侧Tiling库。
其他：npu_op_code_gen：执行代码生成过程，生成aclnn单算子调用代码和入图所需的原型定义代码。
---
## Package类函数
### npu_op_package
创建一个package。
参数说明：
- `（必选）：package的名称。
- TYPE （必选）：package的类型，取值为RUN、SHARED、STATIC。分别对应算子run包形式、算子动态库形式与算子静态库形式。
- [CONFIG]（可选）：用于配置package的内容和安装位置。
- [ENABLE_SOURCE_PACKAGE ]（可选）：是否将源码打包到package中，默认为True。
- [ENABLE_BINARY_PACKAGE ]（可选）：是否将二进制文件打包到package中，默认为True。
- [INSTALL_PATH ]（可选）：指定包的安装路径，默认为CMAKE_BINARY_DIR。
- [ENABLE_CPACK ]（可选）：是否打包，默认为True。对于用户需要定制打包的场景，可以设置为False，配置为False的情况下直接在路径下生成编译产物，不会打包为run包。
示例：
### npu_op_package_add
将目标或文件添加到package中。
参数说明：
- （必选）：package的名称。
- LIBRARY（必选）：指定需要添加到package中的目标名称。
-  [...]（必选）：目标名称列表。
- FILES（必选）：指定需要添加到package中的文件名称。
-  [...]（必选）：文件名称列表。

<!-- cannbot:related:start -->
## 相关

- [C-API asc_simd.h 编译缺 include 根](../../../../../runbooks/compilation/c_api_asc_simd_h_include.md)（`related`）：C-API asc_simd.h 编译缺 include 根 与《CMake函数参考（附录）》的实质衔接是：深层 impl 头实际存在，失败源于 CMake 只加 asc/include 而未加 asc/impl/c_api；C API 入口、官方编译/CMake材料和相邻 include 误用卡用于核对正确头链。
- [CMake arch 子目录隔离 dav-3510 专属 API](../../../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《CMake函数参考（附录）》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../../../runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《CMake函数参考（附录）》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [多算子包组织](../compilation_and_deployment/multi_operator_package.md)（`related`）：CMake函数参考（附录） 与《多算子包组织》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [算子动态库和静态库编译](../compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《CMake函数参考（附录）》说明本文是参考内容，整理算子工程编译过程涉及的CMake函数接口，供需要深入了解编译机制的高级开发者查阅。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [算子编译迁移指导](../../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`related`）：CMake函数参考（附录） 与《算子编译迁移指导》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [编译与部署基本流程](../compilation_and_deployment/basic_process.md)（`related`）：编译与部署基本流程 与《CMake函数参考（附录）》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [运行时加载机制](../invocation/runtime_loading_mechanism.md)（`related`）：CMake函数参考（附录） 与《运行时加载机制》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [附录](appendix.md)（`related`）：CMake 参考给出算子工程编译、链接和目标平台配置函数，是附录所承诺的构建查询入口。
- [高级编程基本流程](../design_and_implementation/host_tiling_implementation.md)（`related`）：高级编程基本流程 与《CMake函数参考（附录）》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [编译过程调试](../compilation_and_deployment/compilation_debug.md)（`same_topic`）：CMake函数参考（附录） 与《编译过程调试》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [高级编程交叉编译](../compilation_and_deployment/cross_compilation.md)（`same_topic`）：高级编程交叉编译 与《CMake函数参考（附录）》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [高级编程编译加速](../compilation_and_deployment/compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《CMake函数参考（附录）》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
