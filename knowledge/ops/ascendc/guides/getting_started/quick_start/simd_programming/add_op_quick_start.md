---
type: Guide
title: Add算子快速入门
description: 本示例是一个入门实践，基于Ascend C SIMD实现Add算子，帮助您快速上手。它完整呈现了Device端核函数实现、Host端调用及编译运行的全流程，助您建立整体认知。开始前，请先参考环境准备安装所需的CANN软件包。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/getting_started/quick_start/simd_programming/add_op_quick_start.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Add算子快速入门

本示例是一个入门实践，基于Ascend C SIMD实现Add算子，帮助您快速上手。它完整呈现了Device端核函数实现、Host端调用及编译运行的全流程，助您建立整体认知。开始前，请先参考环境准备安装所需的CANN软件包。
下面分别介绍基于C API与C++ API的Add算子实现，完整示例代码请参考基于C API实现的Add算子示例和基于C++ API实现的Add算子示例。
- Add算子功能介绍：
Add算子的数学表达式为：
计算逻辑为逐元素完成z = x + y。
- 算子设计
- Device端核函数编程接口
- 核函数定义：通过 __global__修饰符声明。
- 数据分块（Tiling）：使用内置关键字 block_idx确定每个Block负责处理的数据。
- 数据搬入：通过C API接口 asc_copy_gm2ub或C++接口 AscendC::DataCopy完成。
- 数据计算：通过C API接口asc_add或C++接口AscendC::Add完成。
- 数据搬出：通过C API接口asc_copy_ub2gm或C++接口AscendC::DataCopy完成。
- Host端运行时接口
- 内存分配：使用aclrtMallocHost分配Host Memory，aclrtMalloc分配Device Memory。
- 数据搬入：使用aclrtMemcpy将输入数据从Host Memory拷贝到Device Memory。
- 启动NPU计算任务：通过>>语法糖启动核函数。
- 同步等待：调用aclrtSynchronizeStream或aclrtSynchronizeDevice等待任务完成。
- 数据搬出：使用aclrtMemcpy将计算结果从Device Memory拷贝回Host Memory。
- 算子代码实现：
后缀名为*.asc的代码文件包含Host端与Device端代码。

<!-- cannbot:related:start -->
## 相关

- [AscAdd](../../../../apis/simd_api/c_api/vector_compute/asc_add.md)（`explains`）：数据计算：通过C API接口asc_add或C++接口AscendC::Add完成。；执行矢量加法运算。计算公式如下：快速入门明确选择 asc_add 完成计算，API 卡给出该调用的矢量加法与对齐合同，可从教程步骤直接进入接口查阅。
<!-- cannbot:related:end -->
