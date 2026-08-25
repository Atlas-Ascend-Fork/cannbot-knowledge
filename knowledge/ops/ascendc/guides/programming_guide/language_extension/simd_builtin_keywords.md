---
type: Guide
title: SIMD BuiltIn关键字
description: 如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
tags: [task.lookup, topic.programming_model.language_extension]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/language_extension/simd_builtin_keywords.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# SIMD BuiltIn关键字

## 预定义宏
如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一些用户在做异构编程时会经常用到的宏，以及宏的解释。
-   __NPU_ARCH__
__NPU_ARCH__是Device侧AI Core代码中的预处理宏，用于标识AI处理器的架构版本。该宏由四位数字组成，其中前三位数字用于标识AI Core的IP核(Intellectual Property Core)类型，第四位数字标识该AI Core同一个IP核的配置版本。通过该宏，开发者可以针对不同AI处理器，差异化进行代码适配和优化。产品型号和NPU架构版本的对应关系如下：
- Ascend 950PR/Ascend 950DT：3510
- Atlas A3 训练系列产品/Atlas A3 推理系列产品：2201
- Atlas A2 训练系列产品/Atlas A2 推理系列产品：2201
- Atlas 200I/500 A2 推理产品：3002
- Atlas 推理系列产品：2002
- Atlas 训练系列产品：1001
以下为通过__NPU_ARCH__控制在不同AI处理器上算子输出值舍入模式的示例。
-   ASCEND_IS_AIV、ASCEND_IS_AIC
ASCEND_IS_AIV和ASCEND_IS_AIC是通过C++宏实现的条件判断语句，用于在__aicore__修饰的函数中实现代码的条件编译。基于分离模式（AIC核和AIV核分离）开发融合算子时，算子逻辑中同时涉及AIV核和AIC核的处理逻辑，并需要进行核间同步，此时需要通过ASCEND_IS_AIV/ ASCEND_IS_AIC进行AIV和AIC核代码的隔离。
以MatmulNzCustom算子为例，该算子在分离模式下需要分别在AIV核和AIC核上实现不同的逻辑。具体而言，AIV核负责将矩阵数据搬入Unified Buffer，完成数据的重排（将矩阵数据转换为NZ格式），并将其写入Global Memory。而AIC核则直接从Global Memory读取已经重排好的NZ格式数据，并执行矩阵乘法（Matmul）计算。由于AIV核和AIC核的代码逻辑不同，需要通过ASCEND_IS_AIV和ASCEND_IS_AIC宏进行代码隔离，确保在编译时分别生成适用于AIV核和AIC核的代码。
示例伪码如下：
-   ASCENDC_CUBE_ONLY
ASCENDC_CUBE_ONLY是通过C++宏实现的条件判断语句，用于在__aicore__修饰的函数中实现代码的条件编译。
基于分离模式开发非融合算子时，在只有矩阵计算的算子场景下，可以通过设置ASCENDC_CUBE_ONLY，开启纯Cube模式完成Matmul计算，减少消息通信的性能开销，提升算子性能。
