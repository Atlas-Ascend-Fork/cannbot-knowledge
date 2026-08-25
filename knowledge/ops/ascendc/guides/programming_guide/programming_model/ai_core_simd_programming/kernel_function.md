---
type: Guide
title: 核函数（AI Core SIMD编程）
description: 核函数（Kernel Function）是在设备侧并行执行的C/C++函数。它由主机端代码调用，调用时被实例化为多份并行副本，分别调度到多个AI
  Core上运行（每个AI Core被抽象为一个Block）。这些Block利用AI Core的计算能力，协同完成某一算子的计算。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simd_programming/kernel_function.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 核函数

核函数（Kernel Function）是在设备侧并行执行的C/C++函数。它由主机端代码调用，调用时被实例化为多份并行副本，分别调度到多个AI Core上运行（每个AI Core被抽象为一个Block）。这些Block利用AI Core的计算能力，协同完成某一算子的计算。
## 核函数的定义
定义核函数时需要遵循以下规则。
-   使用函数类型限定符和函数执行空间限定符
除了需要按照C/C++函数声明的方式定义核函数之外，还要为核函数加上额外的函数类型限定符。
必须使用__global__函数类型限定符来标识它是一个核函数，可以被>>调用。同时，需要根据算子实际执行的硬件单元，选择以下一种函数执行空间限定符，详情参考函数执行空间限定符：
-   __aicore__：标识该核函数在设备端AI核上执行，不区分具体核类型（通常用于耦合模式）。
-   __vector__：标识该核函数在设备端Vector核上执行，适用于仅包含Vector计算的算子。
-   __cube__：标识该核函数在设备端Cube核上执行，适用于仅包含Cube计算的算子。
-   __mix__：标识该核函数同时在Cube核和Vector核上执行，适用于包含Vector和Cube融合计算的算子。
-   使用变量类型限定符
指针入参变量需要增加变量类型限定符__gm__，表明该指针变量指向Global Memory上某处内存地址。
-   其他规则
1.  规则：核函数必须具有void返回类型。
2.  规则：核函数参数列表需遵循函数参数列表限制。
-   代码示例如下：
## 核函数的调用
在Ascend C算子编程中，根据代码执行空间的不同，函数被严格划分为三类。它们之间的调用关系遵循如下规则：
-   Host侧执行函数：运行于主机端（CPU）。除了支持标准C/C++语义下的同类函数互调外，其核心作用是作为计算任务的发起者，通过内核调用符>>下发执行配置，跨界调用设备侧的核函数。
-   核函数（Kernel Function）：运行于设备端（NPU），是Host侧任务下发的执行入口。核函数在组织并行计算逻辑时，可以向下调用其他的Device侧执行函数。
-   Device侧执行函数：运行于设备端（NPU）的普通函数（除核函数外）。此类函数主要用于封装和复用底层计算逻辑，其调用权限被严格限制在设备侧内部，仅支持被核函数或同类的Device侧执行函数调用。
Host侧通过内核调用符>>的语法形式调用核函数，如下所示：
>>内的参数为核函数的执行配置，由3个参数决定，详细用法请参考核函数配置：
-   numBlocks：规定了核函数将会在几个核上执行，对于不同的硬件架构和算子类型，numBlocks的设置规则有一些区别，详见核函数配置。每个执行该核函数的核会被分配一个逻辑ID，即block_idx，可以在核函数的实现中使用内置变量block_idx获取。
