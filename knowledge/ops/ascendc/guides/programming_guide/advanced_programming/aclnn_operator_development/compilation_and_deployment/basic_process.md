---
type: Guide
title: 编译与部署基本流程
description: 本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/basic_process.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 编译与部署基本流程

本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包*.run。详细的编译操作包括：
-   编译Ascend C算子Kernel侧代码实现文件*.cpp，分为源码发布和二进制发布两种方式。
-   源码发布：不对算子Kernel侧实现进行编译，保留算子Kernel源码文件*.cpp。该方式可以支持算子的在线编译、通过ATC模型转换的方式编译算子的场景。
-   二进制发布：对算子Kernel侧实现进行编译，生成描述算子相关信息的json文件*.json和算子二进制文件*.o。算子调用时，如果需要直接调用算子二进制，则使用该编译方式，比如通过单算子API调用的方式完成单算子的调用，PyTorch框架中单算子调用的场景，动态网络中调用算子的场景。
-   编译Ascend C算子Host侧代码实现文件*.cpp、*.h。
-   将原型定义和shape推导实现编译成算子原型定义动态库libcust_opsproto_*.so，并生成算子原型对外接口op_proto.h。
-   将Tiling实现编译成Tiling动态库liboptiling.so等。
-   基于算子原型定义，自动生成单算子API调用代码和头文件aclnn_*.h，并编译生成单算子API调用的动态库libcust_opapi.so。
上述编译过程示意图如下：
### 基本流程
使用msOpGen生成的工程，已经包含完整CMake结构，不需要单独编写CMakeLists.txt处理；如果需要自行编写CMakeLists.txt，请参考编译组织。以快速入门的AddCustom为例，msOpGen生成的算子工程编译部署只需三步：
1. 修改CMakePresets.json，填写ASCEND_COMPUTE_UNIT（AI处理器型号）和vendor_name（厂商名称）等编译配置选项；
2. 执行./build.sh，生成custom_opp_*.run安装包；
3. 执行./custom_opp_*.run，安装到运行环境。
以下各节详细介绍每一步的选项和细节。
## 编译配置
编译配置选项的必改参数有两个：
参数名称：参数描述：默认值
ASCEND_COMPUTE_UNIT：AI处理器型号，按实际运行芯片配置。："ascendxxx"
vendor_name：自定义算子所属厂商名称，用于形成vendors/安装目录，避免与其他厂商算子包冲突；同一安装路径下vendor_name相同的算子包会安装到同一目录，同名文件会覆盖。："customize"
除上述必改参数外，其他可选编译配置选项详情如下：
STRING：CMAKE_BUILD_TYPE：Release
