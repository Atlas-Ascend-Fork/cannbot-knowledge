---
type: Guide
title: NPU域上板调试（功能调试）
description: NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。
tags: [task.lookup, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/debug_and_tuning/functional_debug/npu_board_debug.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# NPU域上板调试

NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。
## 通过printf打印数据
printf主要用于打印标量和字符串信息，SIMT编程及SIMD编程均支持。
printf示例如下，printf接口的使用说明和具体约束请参考printf。
## SIMD编程通过DumpTensor打印进行调试
DumpTensor是SIMD编程场景独有的打印功能，用于NPU域上板打印指定Tensor的数据。
具体的使用方法如下：
在算子kernel侧实现代码中需要输出日志信息的地方调用DumpTensor接口打印相关内容。
如下所示，srcLocal表示待打印的Tensor；5表示用户的自定义附加信息，比如当前的代码行号；dataLen表示元素个数。DumpTensor接口的使用说明和具体约束请参考DumpTensor。
Dump时，每个block核的dump信息前会增加对应信息头DumpHead（32字节大小），用于记录核号和资源使用信息；每次Dump的Tensor数据前也会添加信息头DumpTensorHead（32字节大小），用于记录Tensor的相关信息。打印结果的样例如下：
## 使用msSanitizer工具进行异常检测
msSanitizer工具是基于AI处理器的异常检测工具，包含了单算子开发场景下的内存检测、竞争检测、未初始化检测和同步检测四个子功能。当前只支持SIMD编程场景的程序调试，暂不支持SIMT编程场景的程序调试。
-   内存检测：工具可以在用户开发算子的过程中，协助定位非法读写、多核踩踏、非对齐访问、内存泄漏以及非法释放等内存问题。同时工具也支持对CANN软件栈的内存检测，帮助用户定界软件栈内存异常发生的模块。
-   竞争检测：工具可以协助用户定位由于竞争风险可能导致的数据竞争问题，包含核内竞争和核间竞争问题。其中，核内竞争包含流水间竞争和流水内竞争。
-   未初始化检测：工具可以协助用户定位由于内存未初始化可能导致的脏数据读取问题。
-   同步检测：工具可以协助用户定位由于前序算子中的未配对同步指令导致的后续算子同步失败的问题。
具体使用方法请参考《msSanitizer用户指南》。
异常检测程序编译
异常检测工具的使用
内存异常报告解析
内存检测异常报告会输出多种不同类型的异常信息，以下将对非法读写给出了简单的异常信息示例：
## 使用msDebug工具进行算子调试
msDebug是一款面向昇腾设备的算子调试工具，用于调试NPU侧运行的算子程序，为算子开发人员提供调试手段，当前只支持SIMD编程场景的程序调试，暂不支持SIMT编程场景的程序调试。msDebug工具支持调试所有的昇腾算子，包含Ascend C算子（Vector、Cube以及融合算子）程序。具体功能包括断点设置、打印变量和内存、单步调试、中断运行、核切换、检查程序状态、调试信息展示、解析Core dump文件，用户可根据实际情况进行选择。

<!-- cannbot:related:start -->
## 相关

- [DumpAccChkPoint](../../../../apis/simd_api/basic_api/debug_interface/onboard_print/dump_acc_chk_point.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《DumpAccChkPoint》提供“打印指定Tensor内容并支持自定义标签，区别于DumpTensor，支持指定偏移位置开始打印Tensor数据。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [DumpTensor](../../../../apis/simd_api/basic_api/debug_interface/onboard_print/dump_tensor.md)（`explains`）：《DumpTensor》说明打印Tensor内容并支持自定义标签，可选传入Shape信息按指定维度排列展示数据。；《NPU域上板调试（功能调试）》说明NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。。二者在DumpTensor/asc_dump、checkpoint、开关和上板调试工具构成设备张量观测链；VF和精度卡给出不可用PRINTF时的替代证据路径上存在可执行的直接衔接。
- [Printf](../../../../apis/utils_api/tuning_interface/printf.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《Printf》提供“SIMD和SIMT编程调试场景下提供格式化输出功能，在算子Kernel侧打印日志信息。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [asc_dump](../../../../apis/utils_api/tuning_interface/asc_dump.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《asc_dump》提供“将对应内存上的数据打印出来，同时支持打印自定义的附加信息（仅支持uint32_t类型的信息），比如打印当前行号等。使用该接口需要包含"utils/debug/asc_dump.h"头文件。该功能主要用于调试和性能分析，通常在调测阶段使用，会对算子性能产生一定影响，生产环境可以通过设置ASCENDC_DUMP=0的方式关闭。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [printf（AI CPU API）](../../../../apis/ai_cpu_api/printf.md)（`explains`）：焦点处理AI CPU printf 的格式化输出、Dump 配额与异构链接约束；NPU域上板调试（功能调试）正文界定“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的”。候选分别给出相同打印能力在通用 Kernel、AI CPU 编译/编程和 NPU/CPU 调试中的实际调用边界。
- [上板打印](../../../../apis/simd_api/basic_api/debug_interface/onboard_print/onboard_print.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《上板打印》提供“上板打印接口集，包含 DumpTensor、DumpAccChkPoint、PrintTimeStamp 等调试输出接口。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [调试接口](../../../../apis/simd_api/basic_api/debug_interface/debug_interface.md)（`explains`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《调试接口》提供“AscendC 调试接口总览，涵盖上板打印、异常检测、CPU 孪生调试、性能统计及 ASCENDC_DUMP 控制说明。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [CPU域孪生调试（功能调试）](cpu_twin_debug.md)（`related`）：CPU 孪生不模拟所有 Device 关键字、同步和硬件行为；NPU 上板调试是后续验证 DumpTensor、内存异常和真实执行的互补路径。
- [运行正常（功能调试）](../../../operator_practice/functional_debug/running_normally.md)（`related`）：NPU 上板调试提供 printf/DumpTensor、msSanitizer 与单步工具，可直接定位 focal 所说的目标硬件崩溃、越界和运行异常。
- [ShowKernelDebugData工具](../../appendix/show_kernel_debug_data_tool.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《ShowKernelDebugData工具》提供“提供Ascend C算子Kernel调测信息的离线解析能力，将导出的bin文件解析为可读格式。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [TilingDebug](../../appendix/common_operations/tiling_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《TilingDebug》提供“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [kernel侧获取Tiling信息不正确](../../appendix/faq/kernel_tiling_info_incorrect.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《kernel侧获取Tiling信息不正确》提供“通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正确。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [核函数运行验证时算子存在精度问题](../../appendix/faq/kernel_precision_issue.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《核函数运行验证时算子存在精度问题》提供“在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [算子调试（功能调试）](../../../operator_practice/functional_debug/operator_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《算子调试（功能调试）》提供“从异构计算章节可以了解到Ascend C算子主要包括Tiling和Kernel实现两部分组成。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [精度正常（功能调试）](../../../operator_practice/functional_debug/accuracy_normal.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《精度正常（功能调试）》提供“性能优化的基础是算子运行得到正确的计算结果。评判计算结果正确性需要有一定的评判标准，即使用已知的正确的输出和实际结果进行比较。优化过程中，每次迭代修改后，都需要验证性能优化的新结果是否满足精度评判标准。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [编译过程调试](../../advanced_programming/aclnn_operator_development/compilation_and_deployment/compilation_debug.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《编译过程调试》提供“本文是扩展内容，介绍算子工程编译过程中的调试方法。算子工程编译涉及代码生成、Host侧编译、Kernel侧编译、打包部署四个阶段，默认输出通常不足以定位根因，下文按阶段介绍调试手段，并附常见错误的诊断方法。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
- [调试与调优概述](../overview.md)（`same_topic`）：《NPU域上板调试（功能调试）》处理“NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是SIMD编程独有功能，用于打印指定Tensor的数据。”。《调试与调优概述》提供“介绍Ascend C算子调试与调优整体方案，涵盖CPU域孪生调试、NPU域上板调试及性能调优工具。”，其具体合同或探针直接接入NPU 上板打印、异常定位、Tiling 调试、精度对比和离线解析流程。
<!-- cannbot:related:end -->
