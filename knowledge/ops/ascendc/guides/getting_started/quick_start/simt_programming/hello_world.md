---
type: Guide
title: Hello World
description: 本入门示例基于Ascend C SIMT实现Hello World算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/simt_programming/hello_world.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Hello World

本入门示例基于Ascend C SIMT实现Hello World算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
开始前请参考环境准备安装所需的CANN软件包，完整样例请参考hello_world。
- Hello World功能介绍：
在NPU上打印Hello World!。
- Device端Kernel实现：
后缀名为*.asc的代码文件包含Host端与Device端代码，其Device端部分示例如下：
- Host端代码实现：
Host端通过>>语法糖调用Device端代码。
- 算子编译与运行：
执行本样例，将打印出核号和Hello World!信息。
如需进一步了解Ascend C的SIMD与SIMT编程模型，请参阅Ascend C编程模型概述。

<!-- cannbot:related:start -->
## 相关

- [扩展语法内置变量](../../../../apis/simt_api/simt_programming_intro/extended_syntax/builtin_variables.md)（`explains`）：SIMT Hello World 打印核号/线程上下文，内置变量卡给出 blockIdx、threadIdx 等执行坐标，是理解样例每个执行实例输出来源的直接前置。
- [Hello World](../simd_programming/hello_world.md)（`related`）：SIMT HelloWorld 对照另一线程模型的最小工程。
- [环境准备](../../environment_setup.md)（`related`）：SIMT HelloWorld 提供另一编程模型的环境冒烟。
- [编程示例（AI Core SIMT编程）](../../../programming_guide/programming_model/ai_core_simt_programming/programming_examples.md)（`related`）：Hello World说明本入门示例基于Ascend C SIMT实现Hello World算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知；对编程示例（AI Core SIMT编程）而言，示例中的线程索引、核函数、内存层级与同步必须共同成立；Hello World 给出从 launch 到输出检查的最小可运行验证。
<!-- cannbot:related:end -->
