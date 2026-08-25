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

<!-- cannbot:related:start -->
## 相关

- [Aclnn算子工程化开发快速入门](../aclnn_quick_start.md)（`related`）：编译与部署基本流程 与《Aclnn算子工程化开发快速入门》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [CMake arch 子目录隔离 dav-3510 专属 API](../../../../../runbooks/compilation/cmake_arch_dav_3510_api.md)（`related`）：CMake arch 子目录隔离 dav-3510 专属 API 与《编译与部署基本流程》的实质衔接是：该故障由根目录 dav-3510 专属源码被 dav-2201 全量编译造成；架构查证/迁移、CMake/编译加速、arch 文档与同类 include/arch 错配卡共同验证源码隔离。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`related`）：编译与部署基本流程 与《CMake函数参考（附录）》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [单算子API调用](../invocation/single_operator_api_call.md)（`related`）：编译与部署基本流程 与《单算子API调用》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [算子功能设计](../design_and_implementation/operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [编译与执行约束说明](../../../compilation_and_execution/operator_compilation/constraints.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《编译与部署基本流程》明确提供“本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [运行时加载机制](../invocation/runtime_loading_mechanism.md)（`related`）：编译与部署基本流程决定 .so、算子包和配置文件的落盘位置，直接影响运行时按路径发现并加载算子实现。
- [高级编程基本流程](../design_and_implementation/kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [多算子包组织](multi_operator_package.md)（`same_topic`）：编译与部署基本流程 与《多算子包组织》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [算子动态库和静态库编译](dynamic_static_lib_compilation.md)（`same_topic`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译与部署基本流程》说明本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译过程调试](compilation_debug.md)（`same_topic`）：编译与部署基本流程 与《编译过程调试》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [高级编程交叉编译](cross_compilation.md)（`same_topic`）：高级编程交叉编译 与《编译与部署基本流程》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [高级编程基本流程](../design_and_implementation/host_tiling_implementation.md)（`same_topic`）：高级编程基本流程 与《编译与部署基本流程》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [高级编程概述](../../operator_graph_development/overview.md)（`same_topic`）：高级编程概述 与《编译与部署基本流程》的实质衔接是：图高级编程概述由基本开发流程展开，并以图编译执行和 tiling 下沉说明 GE 从构图到下发的生命周期；编译部署流程是产物落点。
- [高级编程编译加速](compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《编译与部署基本流程》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
