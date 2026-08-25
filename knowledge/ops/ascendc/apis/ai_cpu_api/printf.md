---
type: API
title: printf（AI CPU API）
description: 该接口提供AI CPU算子Kernel调试场景下的格式化输出功能，默认将输出内容解析并打印在屏幕上。
tags: [task.lookup, topic.implementation.api_layer.aicpu_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/AI-CPU-API/printf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# printf（AI CPU API）

该接口提供AI CPU算子Kernel调试场景下的格式化输出功能，默认将输出内容解析并打印在屏幕上。

函数原型：void printf(const char* fmt, ...)

参数：
- fmt（输入）：格式控制字符串，包含两种类型的对象：普通字符和转换说明。
普通字符将原样不动地打印输出。转换说明并不直接输出而是用于控制printf中参数的转换和打印。每个转换说明都由一个百分号字符（%）开始，，以转换说明结束，从而说明输出数据的类型。

约束：
- 该接口仅支持通过>>调用，并在异构编译场景使用。
- 该接口不支持打印除换行符之外的其他转义字符。
- 该接口使用Dump功能，所有使用Dump功能的接口在每个核上Dump的数据总量不可超过1M。请开发者自行控制待打印的内容数据量，超出则不会打印。
- 使用该接口时，若采用bisheng命令行编译，开发者需要手动链接相关的静态库；而使用CMake编译时，框架会自动处理链接问题，无需开发者额外关注。具体编译命令如下：通过--cce-aicpu-laicpu_api为Device链接libaicpu_api.a，通过--cce-aicpu-L指定libaicpu_api.a的库路径。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [AI CPU算子编译](../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；AI CPU算子编译正文界定“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [AI CPU编程（编程模型）](../../guides/programming_guide/programming_model/ai_cpu_programming.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；AI CPU编程（编程模型）正文界定“AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力，可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算，通常作为AI Core的补充，主要承担非矩阵类、逻辑比较”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [CPU域孪生调试（功能调试）](../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；CPU域孪生调试（功能调试）正文界定“本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当前SIMT编程场景不支持”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [NPU域上板调试（功能调试）](../../guides/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；NPU域上板调试（功能调试）正文界定“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [Printf](../utils_api/tuning_interface/printf.md)（`related`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；Printf正文界定“SIMD和SIMT编程调试场景下提供格式化输出功能，在算子Kernel侧打印日志信息”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
<!-- cannbot:related:end -->
