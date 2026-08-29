---
type: Guide
title: Gather算子快速入门
description: 本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/simt_programming/gather_op_quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Gather算子快速入门

本入门示例基于Ascend C SIMT实现一维Gather算子，带你快速上手实践，涵盖Device端核函数实现、Host端调用以及编译运行的完整流程，帮助开发者建立整体认知。
开始前请参考环境准备安装所需的CANN软件包，完整样例请见Gather。
- Gather算子功能介绍：
Gather算子的数学表达式为：
计算逻辑：根据索引张量index中的每个元素，从一维输入向量input中采集对应位置的数据，并写入输出张量output。
- 算子设计：
- Device端核函数编程接口
- 核函数定义：通过__global__修饰符声明。
- 数据划分：使用内置变量threadIdx、blockIdx、blockDim计算线程索引，并为每个线程分配需要处理的数据元素。
- 数据搬入：无需额外接口，直接通过指针访问即可。
- 数据计算：根据index中的索引值及操作符[]读取输入数据。
- 数据搬出：无需额外接口，直接通过指针访问即可。
- Host端运行时接口
- 内存分配：使用aclrtMallocHost分配Host Memory，aclrtMalloc分配Device Memory。
- 数据搬入：使用aclrtMemcpy将输入数据从Host Memory拷贝到Device Memory。
- 启动NPU计算任务：通过>>语法糖启动核函数。
- 同步等待：调用aclrtSynchronizeStream等待当前Stream上的任务完成，或调用aclrtSynchronizeDevice等待Device上所有任务完成。
- 数据搬出：使用aclrtMemcpy将计算结果从Device Memory拷贝回Host Memory。
- 算子代码实现：
后缀名为*.asc的代码文件包含Host端与Device端代码。
- Device端Kernel实现：
Device端部分示例如下：
- Host端代码实现：
Host端通过>>语法糖调用Device端代码。
- 算子编译与运行：
CMake配置文件示例：
编译并执行：
如需进一步了解Ascend C的SIMD与SIMT编程模型，请参阅Ascend C编程模型概述。
