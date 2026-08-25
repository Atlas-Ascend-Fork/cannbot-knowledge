---
type: Guide
title: 编译与执行约束说明
description: 编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/operator_compilation/constraints.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 约束说明

- 在同一个编译单元，若存在多个核函数，暂不支持自动推导Kernel类型，需要开发者手动设置Kernel类型。
- 特别地，针对如下型号，无论是否是同一个编译单元多个核函数的场景，均不支持在开发者未设置Kernel类型时进行自动推导。建议开发者手动设置Kernel类型。
- Ascend 950PR/Ascend 950DT
- Atlas 推理系列产品
- Kernel函数推荐使用 __cube__ / __vector__ / __mix__(cube, vec)进行标记，KERNEL_TASK_TYPE_DEFAULT接口即将废弃。
- 纯Scalar算子无法实现自动推导
需手动标记Kernel函数类型，推荐设置为纯Vector类型，添加__vector__ attribute进行标记：
- bfloat16_t等数据类型在Host端仅支持以C++模板的形式进行定义与声明，具体数据类型如下：
Ascend 950PR/Ascend 950DT：bfloat16_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、fp8_e8m0_t、fp4x2_e2m1_t、fp4x2_e1m2_t、int4x2_t。
Atlas A2 训练系列产品/Atlas A2 推理系列产品：bfloat16_t。
Atlas A3 训练系列产品/Atlas A3 推理系列产品：bfloat16_t。
- 暂不支持在函数空间外定义和使用device侧的字符串字面量。例如：

<!-- cannbot:related:start -->
## 相关

- [AI Core编译基本用法](ai_core_operator_compilation.md)（`related`）：《AI Core编译基本用法》的任务是“当开发者完成一个Kernel核函数的编写，并在Host侧通过\>\>方式完成核函数的启动调用后，就需要进行算子源码编译与算子运行，接下来我们介绍通过bisheng编译器完成算子编译的基本用法。”。《编译与执行约束说明》具体提供“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”，它直接用于BiSheng AOT 编译、约束、调试、交叉编译和迁移流程。
- [GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型](../../../../runbooks/compilation/get_tiling_data_with_struct.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《GET_TILING_DATA_WITH_STRUCT 宏不接受模板类型》明确提供“GET_TILING_DATA_WITH_STRUCT 宏内部对 tiling_struct 做 # 字符串化拼进 section 名，传入带 <> 的模板类型（如 MaskedFillTilingData<RANK>）会触发 C++ 解析错；用 if constexpr 或 trait 绕开 <> 又会破坏节级 tiling 注册，报 do not registe tiling struct。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [算子动态库和静态库编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/dynamic_static_lib_compilation.md)（`related`）：《算子动态库和静态库编译》说明介绍将自定义算子工程编译为动态库或静态库的方法，支持应用直接链接或集成到其他工程中。；《编译与执行约束说明》说明编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。。二者在SHARED/STATIC产物通过npu_op_package与CMake生成，并分别进入直接链接、运行时加载和常规部署流程上存在可执行的直接衔接。
- [编译与部署基本流程](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/basic_process.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《编译与部署基本流程》明确提供“本文是基础内容，介绍算子Kernel侧和Host侧实现开发完成后，如何对算子工程进行编译、生成自定义算子安装包\.run。详细的编译操作包括：”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [编译过程调试](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《编译过程调试》明确提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [高级编程交叉编译](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/cross_compilation.md)（`related`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《高级编程交叉编译》明确提供“本文是扩展内容，介绍当编译平台与运行平台架构不同时（例如在x86_64开发机上编译、再部署到aarch64边缘设备），如何对算子工程进行交叉编译。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [AI CPU算子编译](ai_cpu_operator_compilation.md)（`same_topic`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《AI CPU算子编译》明确提供“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [毕昇编译器简介](bisheng_compiler.md)（`same_topic`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《毕昇编译器简介》明确提供“毕昇编译器是专为昇腾AI处理器设计的异构编译器，原生支持Ascend C算子代码的编译，可将用户编写的算子程序高效转换为二进制可执行文件或动态库。编译器的可执行文件名为bisheng，支持x86、aarch64等多种主机平台，并直接提供对设备侧AI Core架构的指令集编译支持。借助毕昇编译器，开发者可以更高效、便捷地完成面向昇腾平台的算子开发与优化工作。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
- [编译与执行RTC](rtc_runtime_compilation.md)（`same_topic`）：《编译与执行约束说明》处理“编译与执行约束说明，包含Kernel类型推导、数据类型与字符串字面量等限制。”。《编译与执行RTC》明确提供“RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译成目标机器码，提升程序运行性能。”，其参数、调用或验证步骤直接接入Ascend C 编译约束、AOT/交叉编译、模板宏和编译错误定位。
<!-- cannbot:related:end -->
