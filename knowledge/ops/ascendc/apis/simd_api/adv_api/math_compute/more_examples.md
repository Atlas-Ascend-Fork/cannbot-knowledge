---
type: API
title: 更多样例（数学计算）
description: 下面的样例展示了数学库kernel侧API和Tiling API GetXxxMaxMinTmpSize的配套使用方法，具体流程如下：
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/more_examples.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 更多样例

数学计算高阶API的配套使用样例，展示kernel侧API与Host侧Tiling API的协作流程，包含四个典型场景。

样例一：展示GetXxxMaxMinTmpSize Tiling接口与kernel侧API配套使用。Host侧通过AscendC::TensorShape描述输入shape，调用GetXxxMaxMinTmpSize获取maxValue/minValue，结合PlatformAscendC获取UB剩余空间，选取合适的tmpSize写入tiling data；kernel侧读取tiling data分配临时空间并调用高阶API（以Asin为例）。

样例二：展示PlatformAscendC::ReserveLocalMemory与kernel侧API配合使用。通过ReserveLocalMemory预留内存空间，GetCoreMemSize获取实际可用UB大小，基于此计算最大支持Shape，避免多次调用GetXxxMaxMinTmpSize。kernel侧调用不带临时空间参数的API（接口框架自动申请），执行多种数学运算。

样例三：展示GetXxxTmpBufferFactorSize Tiling接口与kernel侧API配套使用。Host侧获取maxLiveNodeCount和extraBuf，结合可用临时空间currBuff推算单次最大计算元素数量currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCount / typeSize，取多个API推算结果的最小值，实现分块计算（以Asin+Acos链式调用为例）。

样例四：以Exp接口为例展示模板参数isReuseSource的使用。isReuseSource为false时接口内部不复用源操作数内存，srcTensor保持原值；为true时接口内部复用srcTensor内存空间存放中间结果以节省内存，但接口执行完成后srcTensor不再是原始值。该参数仅在float数据类型时生效。
