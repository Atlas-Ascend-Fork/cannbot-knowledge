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
