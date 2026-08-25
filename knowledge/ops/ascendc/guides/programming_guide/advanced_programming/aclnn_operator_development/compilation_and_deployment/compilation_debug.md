---
type: Guide
title: 编译过程调试
description: 本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 编译过程调试

本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。
## 生成代码调试
npu_op_code_gen在cmake configure阶段自动生成aclnn调用代码和算子原型定义代码。生成产物位于ASCEND_AUTOGEN_PATH目录，默认是/autogen；按本文示例使用build_out时，对应目录为build_out/autogen。当原型定义有误或生成结果与预期不符时，需要检查这些文件。
### 生成产物目录
以AddCustom工程为例，配置完成后build_out/autogen/下会生成aclnn调用代码、算子原型定义代码和若干编译配置文件。下方仅列出排查代码生成问题时常用的关键产物；多算子工程会为每个算子生成对应的aclnn_.cpp和aclnn_.h。
### 常见问题排查场景
问题：查看什么
aclnn接口参数与原型定义不匹配：检查aclnn_.h中的函数签名，确认输入输出和属性参数是否正确映射。
入图场景算子注册信息异常：检查op_proto.cc中的注册宏，确认OpType、dtype/format是否与Host侧定义一致。
某个算子的调用代码未生成：检查npu_op_code_gen的SRC参数是否包含了该算子的Host侧源文件。
JOIN_OP_DEF相关芯片型号异常：JOIN_OP_DEF=True时算子构建阶段不再显式传入ASCEND_COMPUTE_UNIT，需结合configure日志、op_proto.cc中的AddConfig和CMakePresets.json中的芯片型号确认目标型号是否被覆盖。
### 强制重新生成
修改文件后，如果怀疑历史产物残留导致问题，可以手动清理后重新configure：
## Host侧编译调试
Host侧构建时，默认只输出编译目标的摘要信息，不显示实际执行的编译和链接命令。通过VERBOSE机制可以打印完整的命令行，用于排查头文件路径、链接库、编译选项等问题。
### 方式一：构建时开启verbose
在构建命令中指定verbose，打印每条编译和链接命令：
输出示例：
每行输出包含完整的编译器调用，可以看到：
- 实际的编译器路径（如/usr/bin/c++）。
- 宏定义（-D）和头文件搜索路径（-I）。
- 编译选项（如-fvisibility=hidden、-g、-O2）。
- 链接库路径（-L）和链接库（-l）。
### 方式二：cmake配置CMAKE_VERBOSE_MAKEFILE
在cmake configure阶段开启verbose，后续所有make调用都会自动打印完整命令：
与方式一效果相同，区别在于设置持久化在CMakeCache.txt中，无需每次构建时重复指定。
### 常见问题排查场景
问题：查看什么
头文件找不到

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](../../../compilation_and_execution/operator_compilation/ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《编译过程调试》具体提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [毕昇编译器简介](../../../compilation_and_execution/operator_compilation/bisheng_compiler.md)（`related`）：《编译过程调试》明确“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”；它与《毕昇编译器简介》的“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”在实际调用参数、数据流或结果校验上直接衔接。
- [算子动态库和静态库编译](dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译过程调试》说明本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译与执行约束说明](../../../compilation_and_execution/operator_compilation/constraints.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《编译过程调试》明确提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [CMake函数参考（附录）](../appendix/cmake_function_reference.md)（`same_topic`）：CMake函数参考（附录） 与《编译过程调试》的实质衔接是：CMake 函数参考中的工程函数由算子开发、编译选项、编译脚本、库编译和 UT 指南实际消费；FAQ 卡验证其构建阶段失败信号。
- [NPU域上板调试（功能调试）](../../../debug_and_tuning/functional_debug/npu_board_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《编译过程调试》提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [编译与部署基本流程](basic_process.md)（`same_topic`）：编译与部署基本流程 与《编译过程调试》的实质衔接是：编译部署流程直接分支到动态/静态库、交叉编译、调试、加速、多算子包、CMake 和运行时加载；arch 子目录故障验证 SoC 专属源码必须在构建期隔离。
- [高级编程交叉编译](cross_compilation.md)（`same_topic`）：高级编程交叉编译 与《编译过程调试》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [高级编程基本流程](../design_and_implementation/host_tiling_implementation.md)（`same_topic`）：高级编程基本流程 与《编译过程调试》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
- [高级编程编译加速](compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《编译过程调试》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
