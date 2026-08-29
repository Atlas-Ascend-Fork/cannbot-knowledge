---
type: Guide
title: AI CPU编程（编程模型）
description: AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力，可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算，通常作为AI
  Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。AI CPU的运行环境为基础的Linux环境，编程时可使用libc库，C++标准库，STL模板库等。其硬件架构图如下所示：
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/programming_model/ai_cpu_programming.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AI CPU编程

AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力，可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算，通常作为AI Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。AI CPU的运行环境为基础的Linux环境，编程时可使用libc库，C++标准库，STL模板库等。其硬件架构图如下所示：
本节介绍的AI CPU编程仅支持如下产品型号：
-   Ascend 950PR/Ascend 950DT
-   Atlas A3 训练系列产品/Atlas A3 推理系列产品
-   Atlas A2 训练系列产品/Atlas A2 推理系列产品
## AI CPU核函数定义
在进行AI CPU编程时，与AI Core类似，同样需要定义设备侧函数入口（即核函数），该函数必须通过__aicpu__标识符进行声明，并且需与__global__标识符联合使用以表明其只能被Host侧调用。AI CPU的Device侧实现文件需要以.aicpu为后缀（或者以.cpp为后缀，在编译时增加-x aicpu选项）。该实现文件中包括上面介绍的核函数以及AI CPU普通函数定义，AI CPU普通函数无需添加执行空间标识符。
如下是一个AI CPU“Hello World”程序的示例，hello_world.aicpu文件内容如下：
## AI CPU核函数调用
AI CPU核函数的调用需要在.asc文件中进行，和AI Core的算子调用类似，同样使用>>语法。
-   numBlocks：AI CPU Device侧暂不支持分核逻辑，因此Host侧调用多核无实际意义。建议设置为1。
-   l2ctrl：保留参数，当前固定为nullptr，开发者无需关注。
-   stream：类型为aclrtStream，stream用于维护一些异步操作的执行顺序，确保按照应用程序中的代码调用顺序在Device上执行。stream创建等管理接口请参考《Runtime运行时API》。
加载和运行算子时，需要使用Runtime API，完成运行时管理和配置，详细内容请参考算子运行。AI CPU算子的编译请参考AI CPU算子编译。
## AI CPU模板核函数
若需要使用模板核函数，则需要在.aicpu文件中给出模板核函数的实例化声明，参考如下：
并在.asc文件中新增模板核函数实例化的extern声明：
## 更多进阶用法
