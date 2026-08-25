---
type: Guide
title: AI Core编译基本用法
description: 当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/ai_core_operator_compilation.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AI Core编译基本用法

当开发者完成一个Kernel核函数的编写，并在Host侧通过>>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。
## AI Core SIMD编译
使用bisheng编译Ascend C源文件的基本命令如下，其中--npu-arch=dav-\用于指定AI处理器架构版本：
bisheng可以通过-I \指定头文件路径、-L \ 指定链接库路径、-l \指定需要链接的动态库或静态库、-D\=\指定宏定义，示例如下：
AI Core SIMD的基本编译流程如下：Host代码使用Host编译器编译成Host二进制，AI Core SIMD代码分为Cube代码和Vector代码，需分别编译成Cube二进制和Vector二进制，先将Cube二进制和Vector二进制链接成Fatbin文件，再与Host二进制合并生成可执行二进制。
- 异构编译，完整样例请参考LINK。
- 单独编译，完整样例请参考LINK。
bisheng异构编译默认采用的是全程序编译模式，该模式要求单个源文件X.asc中编译的设备程序没有任何未解析的外部设备函数和变量引用。设备函数可以调用其他编译单元中定义的设备函数或访问其中定义的设备变量，但必须在bisheng命令行中指定-dc编译选项，才能启用不同编译单元间设备代码的链接功能。这种支持跨编译单元链接设备代码与符号的能力，被称为单独编译。
单独编译能实现更灵活的代码组织、缩短编译耗时，并生成体积更小的可执行文件；相较于全程序编译，它会增加一定的编译构建复杂度。此外，设备代码链接可能会影响程序性能，这也是该模式未被设为默认模式的原因。链接时优化（LTO）可有效降低单独编译带来的性能损耗。
单独编译的强制要求：
- 在一个编译单元中定义的非常量设备变量，在其他编译单元中引用时，必须使用extern关键字声明；
- 所有常量设备变量，定义和跨单元引用时都必须使用extern关键字；
- 所有Ascend C源文件（.asc）都必须使用-dc选项编译。
下方示例中，add_compute.asc定义了变量和函数，add_kernel.asc对其进行引用；两个文件将分别编译，最终链接为完整可执行文件。
- 动态库编译，完整样例请参考LINK。
- 静态库编译，完整样例请参考LINK。
## AI Core SIMT编译
使用bisheng编译器编译Ascend C SIMT源文件时，需要在AI Core SIMD编译的基本命令上增加--enable-simt，示例如下：
AI Core SIMT的基本编译流程如下：Host代码使用Host编译器编译成Host二进制，AI Core SIMT代码编译成SIMT二进制，先将SIMT二进制链接成Fatbin文件，再与Host二进制合并生成可执行二进制。

<!-- cannbot:related:start -->
## 相关

- [AOT编译优化（高级编程）](../../advanced_programming/aot_compilation_optimization.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《AOT编译优化（高级编程）》具体提供“AOT（Ahead-of-Time，提前编译）编译优化是一种将运行时参数提前到编译阶段常量化的性能优化技术。通过在编译阶段对Kernel进行额外的常量化编译，在运行时根据Tiling参数自动匹配预编译的特化版本，让编译器能够进行更深度的优化（如循环展开、死代码消除、常量传播等），从而获得超越通用版本的执行性能。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [图编译和图执行](../../advanced_programming/operator_graph_development/graph_compilation_and_execution.md)（`related`）：图中 AI Core 节点需先生成可加载 kernel binary，是图编译阶段的底层依赖。
- [核函数（AI Core SIMT编程）](../../programming_model/ai_core_simt_programming/kernel_function.md)（`related`）：AI Core 编译说明给出如何把包含 SIMT Kernel 的源文件按目标 npu-arch 编译、链接为可执行产物，是核函数声明和 Host 启动之后的构建落地步骤。
- [毕昇编译器简介](bisheng_compiler.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《毕昇编译器简介》具体提供“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [算子动态库和静态库编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《AI Core编译基本用法》说明当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [算子编译迁移指导](../../../cross_gen_migration_guide/3510_arch_migration/2201_to_3510_guide/op_compilation_migration.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《算子编译迁移指导》具体提供“进行算子编译时，开发者需要感知不同架构、不同的AI处理器型号。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [编译与执行约束说明](constraints.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《编译与执行约束说明》具体提供“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [编译过程调试](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《编译过程调试》具体提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [高级编程交叉编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《高级编程交叉编译》具体提供“本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [高级编程基本流程](../../advanced_programming/aclnn_operator_development/design_and_implementation/kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《AI Core编译基本用法》说明当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [高级编程编译加速](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《AI Core编译基本用法》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
