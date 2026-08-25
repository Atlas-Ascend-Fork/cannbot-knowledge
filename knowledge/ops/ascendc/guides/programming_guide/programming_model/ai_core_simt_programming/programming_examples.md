---
type: Guide
title: 编程示例（AI Core SIMT编程）
description: 基于SIMT进行算子开发需要使用的内置关键字和API请参见SIMT BuiltIn关键字、SIMT语言扩展层C API。当前SIMT编程暂不支持部分语法结构，相关限制请参考语法限制。
tags: [task.lookup, topic.programming_model.execution_model.simt]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_core_simt_programming/programming_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 编程示例

基于SIMT进行算子开发需要使用的内置关键字和API请参见SIMT BuiltIn关键字、SIMT语言扩展层C API。当前SIMT编程暂不支持部分语法结构，相关限制请参考语法限制。
考虑如下计算场景：从形状为100000 * 128的二维向量中获取指定索引所对应的12288行数据。算子输出output第i行数据的计算公式为：
在核函数中完成一行数据量的计算逻辑，通过配置多个线程完成不同行的数据计算操作。核函数的实现逻辑具体为：
-   通过每个线程独有的线程索引找到当前线程需要计算的数据偏移量。
一个线程完成一次核函数的计算操作，核函数内通过计算blockIdx.x * blockDim.x + threadIdx.x得到索引偏移，其中blockIdx是当前线程块的索引，blockDim是每个线程块启用的线程数，threadIdx是当前线程在线程块内的索引，更多详细介绍请参考SIMT BuiltIn关键字。
-   通过下标偏移将偏移位置的输入数据拷贝到输出中，从而完成获取指定数据的功能。
核函数的实现参考如下代码。完整的样例请参考简单gather算子样例。
算子需要处理总共12288行数据，每行数据由核函数完成处理，因此需要12288个线程来完成对所有数据的处理。在Host侧通过>>调用核函数，同时设置启动48个线程块、每个线程块包含256个线程，示例代码如下。
