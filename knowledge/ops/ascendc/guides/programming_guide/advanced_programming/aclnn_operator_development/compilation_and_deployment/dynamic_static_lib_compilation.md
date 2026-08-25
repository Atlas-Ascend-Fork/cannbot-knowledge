---
type: Guide
title: 算子动态库和静态库编译
description: 介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/dynamic_static_lib_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 算子动态库和静态库编译

本文是扩展内容，介绍如何将自定义算子工程编译为动态库或静态库，并在应用程序或图模式场景中使用这些库。常规部署场景优先参考编译与部署基本流程生成custom_opp_*.run算子包；只有当应用需要直接链接算子库，或希望把算子库集成到其他工程中时，再考虑使用动态库或静态库编译。与.run算子包预先安装到OPP目录不同，动态库或静态库方式在进程拉起后会由运行时创建临时目录，将算子包结构恢复到临时目录中并从该目录加载算子相关文件，进程退出前再删除该临时目录。
## 算子动态库和静态库
算子动态库和静态库编译，是将算子Kernel实现、Host侧Tiling实现、入图适配文件，以及自动生成的单算子调用代码编译链接成库文件的过程。编译后会同时生成单算子调用aclnn头文件和算子原型定义头文件，分别用于单算子调用和算子入图场景。
和.run算子包相比，动态库或静态库更适合被应用工程直接链接；.run算子包更适合安装到OPP的vendors/路径后供运行环境使用。不同产物形态的典型使用方式如下。
产物形态：CMake配置：主要产物：典型使用方式
算子包：TYPE RUN：custom_opp_*.run：安装到OPP的vendors/路径，供运行环境使用。
动态库：TYPE SHARED：libcust_opapi.so：应用或图模式流程动态链接。
静态库：TYPE STATIC：lib${vendor_name}.a：应用工程静态链接，通过aclnn方式执行算子。
算子动态库和静态库编译支持以下产品范围：
- Ascend 950PR/Ascend 950DT
- Atlas A3训练系列产品 / Atlas A3推理系列产品
- Atlas A2训练系列产品 / Atlas A2推理系列产品
开始前需完成以下准备：
- 已完成算子原型定义、Host侧Tiling实现和Kernel侧实现；
- 工程使用find_package(ASC)和npu_op_package组织编译；
- 已配置CANN环境变量，例如执行source ${install_path}/cann/set_env.sh；
- 已在CMakePresets.json或CMake命令中配置vendor_name、ASCEND_COMPUTE_UNIT、CMAKE_INSTALL_PREFIX等参数。
## 编译动态库
动态库编译时，将npu_op_package的TYPE设置为SHARED。以快速入门里的AddCustom为例，将顶层CMakeLists.txt里的npu_op_package配置修改如下：
执行编译和安装：
编译成功后，主要产物位于${CMAKE_INSTALL_PREFIX}：
## 编译静态库
静态库编译时，将npu_op_package的TYPE设置为STATIC。
