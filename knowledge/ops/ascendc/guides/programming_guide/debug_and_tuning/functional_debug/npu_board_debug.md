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
