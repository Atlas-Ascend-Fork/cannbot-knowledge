---
type: Guide
title: 高级编程交叉编译
description: 本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 交叉编译

本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。
## 概述
完成算子代码实现后，如果编译平台和运行平台架构一致，直接参考基本流程编译即可。如需交叉编译（编译平台架构与运行平台架构不同），参考本文档。
交叉编译的典型场景：
- 在x86_64开发机上编译，部署到aarch64边缘设备。
- 在aarch64服务器上编译，部署到x86_64服务器。
## 交叉编译工具下载
以Ubuntu系列操作系统为例，交叉编译工具下载命令如下表所示。其他操作系统请替换为实际的下载命令。
当前平台架构：运行环境平台架构：编译工具下载命令
x86_64：aarch64：sudo apt-get install -y g++-aarch64-linux-gnu
aarch64：x86_64：sudo apt-get install -y g++-x86-64-linux-gnu
安装完成后，可通过以下命令验证工具是否可用：
## CMakePresets.json配置
交叉编译需修改算子工程目录下CMakePresets.json的两个配置项：
### 使能交叉编译
将ENABLE_CROSS_COMPILE设置为True：
### 指定交叉编译工具路径
使用which命令查找交叉编译工具的安装路径：
假设安装在 /usr/bin/ 下，将CMAKE_CROSS_PLATFORM_COMPILER设置为交叉编译工具的安装路径：
## 执行交叉编译
交叉编译Kernel二进制时，编译框架需要先加载本机架构可执行的Tiling动态库来获取编译参数。因此设置完ENABLE_CROSS_COMPILE=True且ENABLE_BINARY_PACKAGE=True之后，需要执行两步才能完成交叉编译：
- 要先在本机模式下生成libcust_opmaster_rt2.0.so；
- 再通过HOST_NATIVE_TILING_LIB传给交叉编译阶段。
下面以快速入门里的AddCustom、在aarch64编译机上生成x86_64目标算子包为例演示：
建议本机Tiling库和交叉编译产物使用两个不同的构建目录，避免本机架构产物和目标架构产物混在一起：
- build_native_tiling：只用于生成本机架构可加载的Tiling动态库。
- build_out：用于生成目标架构的算子包。
步骤1：本机模式生成Tiling库
HOST_NATIVE_TILING_LIB指向的是本机架构动态库。例如当前编译机是aarch64时，该库应为aarch64动态库。

<!-- cannbot:related:start -->
## 相关

- [aclrtcCompileProg](../../../../../apis/utils_api/rtc/aclrtc_compile_prog.md)（`explains`）：高级编程交叉编译 与《aclrtcCompileProg》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [aclrtcGetCompileLog](../../../../../apis/utils_api/rtc/aclrtc_get_compile_log.md)（`explains`）：高级编程交叉编译 与《aclrtcGetCompileLog》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [aclrtcGetCompileLogSize](../../../../../apis/utils_api/rtc/aclrtc_get_compile_log_size.md)（`explains`）：高级编程交叉编译 与《aclrtcGetCompileLogSize》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [AI Core编译基本用法](../../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《高级编程交叉编译》具体提供“本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [C-API asc_simd.h 编译缺 include 根](../../../../../runbooks/compilation/c_api_asc_simd_h_include.md)（`related`）：C-API asc_simd.h 编译缺 include 根 与《高级编程交叉编译》的实质衔接是：深层 impl 头实际存在，失败源于 CMake 只加 asc/include 而未加 asc/impl/c_api；C API 入口、官方编译/CMake材料和相邻 include 误用卡用于核对正确头链。
- [毕昇编译器简介](../../../compilation_and_execution/operator_compilation/bisheng_compiler.md)（`related`）：高级编程交叉编译 与《毕昇编译器简介》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [算子动态库和静态库编译](dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《高级编程交叉编译》说明本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译与执行RTC](../../../compilation_and_execution/operator_compilation/rtc_runtime_compilation.md)（`related`）：高级编程交叉编译 与《编译与执行RTC》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [编译与执行约束说明](../../../compilation_and_execution/operator_compilation/constraints.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《高级编程交叉编译》明确提供“本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`same_topic`）：高级编程交叉编译 与《CMake函数参考（附录）》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [编译与部署基本流程](basic_process.md)（`same_topic`）：高级编程交叉编译 与《编译与部署基本流程》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [编译过程调试](compilation_debug.md)（`same_topic`）：高级编程交叉编译 与《编译过程调试》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [运行时加载机制](../invocation/runtime_loading_mechanism.md)（`same_topic`）：高级编程交叉编译 与《运行时加载机制》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [高级编程编译加速](compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《高级编程交叉编译》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
