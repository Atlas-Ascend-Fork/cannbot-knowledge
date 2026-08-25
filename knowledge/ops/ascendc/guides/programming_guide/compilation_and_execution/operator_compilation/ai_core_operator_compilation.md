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
