---
type: Guide
title: 技术附录函数
description: 核函数的参数列表（argument list）仅支持以下类型：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/syntax_restrictions/functions.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 函数

## 核函数参数列表限制
核函数的参数列表（argument list）仅支持以下类型：
- 基础数据类型，如int32_t、float等。
- 基础数据类型组成的结构体，支持嵌套结构体形式，但必须为POD（Plain Old Data）类型。
- 基础数据类型的指针类型，如int32_t*、float*等，实际上这些指针指向的是Global Memory内存。
## SIMT VF函数限制
__simt_vf__标记的SIMT VF函数需要遵循以下约束和限制：
-   标量参数不允许使用指针和引用。
-   不允许将栈数组作为参数传入SIMT VF函数；SIMT VF函数的指针形参必须显式使用__gm__或__ubuf__地址空间限定符。以下错误示例会在编译期报错。
-   如果传参中出现多级指针，不允许使用内层栈地址指针访问，以下为错误示例。
-   不支持通过函数指针进行间接调用，被调用的__simt_vf__函数需要在编译期确定。
-   函数的inline行为由编译器决定，添加的always_inline或noinline将被忽略。
-   不允许使用结构体作为参数，以下为错误示例。
## SIMD与SIMT混合编程场景结构体使用限制
SIMD与SIMT混合编程场景下，当使用位于Global Memory或Unified Buffer中的结构体或类拷贝构造新结构体或类时，需要开发者为结构体或类手动实现拷贝构造函数，编译器不会默认隐式生成。
在异构编译场景中，Host和Device可共用结构体定义代码，但Host侧无法识别__callee__、__gm__等Device侧关键字，因此无法根据这些关键字实现函数重载。当需要定义多个地址空间重载函数时，需通过宏__NPU_ARCH__将相关Device代码隔离，以避免函数定义冲突。__NPU_ARCH__是由编译预定义的宏，可用于区分Device侧代码，具体可参考《毕昇编译器》中的“基本编程指导 > AI Core编程指导 > 预定义宏和内建变量”章节。
此外，SIMD与SIMT混合编程场景下不支持直接向Global Memory或Unified Buffer地址空间写入结构体。
