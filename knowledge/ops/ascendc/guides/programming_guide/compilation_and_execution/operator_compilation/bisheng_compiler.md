---
type: Guide
title: 毕昇编译器简介
description: 毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI
  Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/bisheng_compiler.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 毕昇编译器简介

毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。

目前，编译器支持如下型号：

-   Ascend 950PR/Ascend 950DT

-   Atlas A3 训练系列产品/Atlas A3 推理系列产品

-   Atlas A2 训练系列产品/Atlas A2 推理系列产品

-   Atlas 推理系列产品

毕昇编译器支持的源码文件和头文件包括：.c（C 源码，Host-only 代码）、.cpp/.cc/.cxx（C++ 源码，Host-only 代码）、.h/.hpp/.hh/.hxx（C/C++ 头文件，支持 Device、Host 及混合代码）和 .asc（Ascend C 源码，支持 Device、Host 及混合代码）。

-   异构编译场景中的编程相关约束请参考约束说明。
-   如果需要了解更多的毕昇编译器的基础知识，详细内容请参考[《毕昇编译器用户指南》](https://www.hiascend.com/document/redirect/CannCommunityBiSheng)。
