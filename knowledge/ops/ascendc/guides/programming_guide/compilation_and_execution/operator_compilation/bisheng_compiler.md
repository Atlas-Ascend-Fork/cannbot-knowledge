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

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《毕昇编译器简介》具体提供“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav](../../../../runbooks/compilation/bisheng_npu_arch_requires_lowercase_dav_2201.md)（`related`）：bisheng 拒绝大写 --npu-arch=DAV2201 须用小写 dav 与《毕昇编译器简介》的实质衔接是：故障根因是把 DAV_2201 内部名误写成 bisheng 参数；架构查证链、GetCurNpuArch、dav-3510 同类 CMake 隔离、编译器/迁移文档和 CMake 参考共同确认 token 映射与全量重配。
- [编译过程调试](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md)（`related`）：《编译过程调试》明确“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”；它与《毕昇编译器简介》的“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”在实际调用参数、数据流或结果校验上直接衔接。
- [高级编程交叉编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`related`）：高级编程交叉编译 与《毕昇编译器简介》的实质衔接是：交叉编译需先生成本机 tiling 库再构建目标包；基本编译、CMake、runtime、compiler/RTC/compile-log 接口共同支撑配置和诊断。
- [编译与执行约束说明](constraints.md)（`same_topic`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《毕昇编译器简介》明确提供“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [高级编程编译加速](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_acceleration.md)（`same_topic`）：高级编程编译加速 与《毕昇编译器简介》的实质衔接是：编译加速围绕 ccache、选择性编译、并行度和增量构建；编译/交叉编译/库/CMake/AOT/BiSheng 与 arch 源隔离材料对应这些可执行构建阶段。
<!-- cannbot:related:end -->
