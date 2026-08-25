---
type: Guide
title: 技术附录概述
description: Host侧与clang15一致，支持完整的C/C++标准。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/technical_appendix/cpp_standard_support/overview.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 技术附录概述

Host 侧与 clang15 一致，支持完整的 C/C++ 标准，开发者可使用标准库的完整功能进行 Host 侧编程。
Device 侧默认支持 C++11 标准，可通过编译选项指定 C++14、C++17 或 C++20 标准，以使用更高版本的 C++ 语言特性。
由于昇腾 AI Core 硬件限制，部分 C++ 运行时能力无法支持，例如动态内存分配和异常处理等依赖运行时环境的特性。
Host 侧与 Device 侧的 C++ 标准支持范围不同，涉及跨侧调用的代码需分别考虑标准兼容性，确保编译正确。
