---
type: Guide
title: 基础矢量算子
description: 基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/vector_programming/basic_vector_operator.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础矢量算子

基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。
-   算子分析：分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要调用的Ascend C接口。
-   核函数定义：定义Ascend C算子入口函数。
-   根据矢量编程范式实现算子类：完成核函数的内部实现，包括3个基本任务：CopyIn，Compute，CopyOut。
下文以输入为half数据类型且shape的最后一维为32Bytes对齐、在单核上运行的、一次完成计算的Add算子为例，对上述步骤进行详细介绍。
## 算子分析
算子分析具体步骤如下：
1.  明确算子的数学表达式及计算逻辑。
Add算子的数学表达式为：
计算逻辑是：Ascend C提供的矢量计算接口的操作元素都为LocalTensor，输入数据需要先从外部存储（Global Memory）搬运进片上存储（Unified Buffer），然后使用计算接口完成两个输入参数相加，得到最终结果，再搬出到外部存储上。Ascend C  Add算子的计算逻辑如下图所示。
2.  明确输入和输出。
-   Add算子有两个输入：x与y；输出为z。
-   本样例中算子的输入支持的数据类型为half（float16），算子输出的数据类型与输入的数据类型相同。
-   算子输入支持的shape为（1，2048），输出shape与输入shape相同。
-   算子输入支持的format为：ND。
3.  确定核函数名称和参数。
-   您可以自定义核函数名称，本样例中核函数命名为vec_add_custom。
-   根据对算子输入输出的分析，确定核函数有3个参数x，y，z；x，y为输入在Global Memory上的内存地址，z为输出在Global Memory上的内存地址。
4.  确定算子实现所需接口。
-   实现涉及外部存储和内部存储间的数据搬运，查看Ascend C  API参考中的数据搬运接口，需要使用DataCopy来实现数据搬运。
-   本样例只涉及矢量计算的加法操作，查看Ascend C  API参考中的矢量计算接口，初步分析可使用基础算术Add接口Add实现x+y。
-   使用Queue队列管理计算中使用的Tensor数据结构，具体使用EnQue、DeQue等接口。
通过以上分析，得到Ascend C  Add算子的设计规格如下：
-   算子类型（OpType）：Add
-   算子输入输出：
Add算子输入输出规格
-   核函数名称：vec_add_custom
-   使用的主要接口：
-   DataCopy：数据搬移接口
-   Add：矢量基础算术接口
-   EnQue、DeQue等接口：Queue队列管理接口
-   算子实现文件名称：vector_add.asc
## 核函数定义
根据核函数中介绍的规则进行核函数的定义。
