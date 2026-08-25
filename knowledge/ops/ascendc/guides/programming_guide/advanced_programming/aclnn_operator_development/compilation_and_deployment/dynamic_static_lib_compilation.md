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

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](../../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《AI Core编译基本用法》说明当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《Aclnn算子工程化开发快速入门》说明本文是基础内容，通过一个完整的AddCustom算子示例，帮助您在5分钟内跑通从创建工程、补充算子实现、编译部署到单算子API调用验证的端到端流程。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [C-API asc_simd.h 编译缺 include 根](../../../../../runbooks/compilation/c_api_asc_simd_h_include.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《C-API asc_simd.h 编译缺 include 根》说明在 Ascend 950（dav-3510 / npu_arch_3510, CANN 9.1.0）下用自写 CMakeLists 编译含 `#include "c_api/asc_simd.h"` 的 .asc 时，报 `fatal error: 'instr_impl/npu_arch_3510/vector_datamove_impl/asc_set_gm2ub_pad_impl.h' file not found`。表象像 CANN 安装损坏，实为 include 根选错：C-API 公共头内部以 `instr_impl/...` 相对路径 #include 兄弟内部实现头，仅当 `asc/`（符号链接到 x86_64-linux/asc，下含并列的 include/ 与 impl/）作为 include 根时才解析成功。官方 mmad 样例用 `include_directories("${ASCEND_HOME}/asc/")` 即可编译。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《CMake函数参考（附录）》说明本文是参考内容，整理算子工程编译过程涉及的CMake函数接口，供需要深入了解编译机制的高级开发者查阅。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [单算子API调用](../invocation/single_operator_api_call.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《单算子API调用》说明本文是基础内容，介绍单算子API调用——即通过C/C++调用aclnn接口完成异构计算的过程。aclnn接口和实现已经随自定义算子包交付，因此调用前需要先完成自定义算子包部署。运行时需要可用NPU环境；计算过程中使用的输入输出Tensor、Device内存、workspace、stream等资源由调用方负责申请和释放。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [多算子包组织](multi_operator_package.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《多算子包组织》说明本文是扩展内容，介绍开发多个自定义算子时，如何决定这些算子的发布与部署方式——是全部放在一个算子包中，还是拆成多个算子包。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译与执行约束说明](../../../compilation_and_execution/operator_compilation/constraints.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译与执行约束说明》说明编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译过程调试](compilation_debug.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译过程调试》说明本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [运行时加载机制](../invocation/runtime_loading_mechanism.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《运行时加载机制》说明本文是扩展内容，介绍算子开发完成后，编译产物如何被加载和执行，以及开发时的设计决策如何影响运行表现。本文从算子开发者视角梳理运行时调用的基本模型和代码写法对运行行为的影响。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [高级编程交叉编译](cross_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《高级编程交叉编译》说明本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [高级编程编译加速](compilation_acceleration.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《高级编程编译加速》说明本文是扩展内容，介绍如何降低算子工程的编译耗时。算子工程编译耗时主要来自Kernel侧代码的逐芯片、逐TilingKey编译；本文从缓存复用、选择性编译、并行度和增量构建四个维度给出加速方案。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [如何开发动态输入算子](../../../appendix/common_operations/develop_dynamic_input_operator.md)（`same_topic`）：如何开发动态输入算子 与《算子动态库和静态库编译》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [编译与部署基本流程](basic_process.md)（`same_topic`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
<!-- cannbot:related:end -->
