---
type: Guide
title: AIC和AIV独立运行机制
description: AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不依赖消息驱动，开启双主模式能够提高Matmul计算性能。默认情况下，双主模式不开启，需要通过MatmulConfig中的enableMixDualMaster参数开启。
tags: [task.lookup, topic.programming_model.execution_model.simd]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/aic_aiv_independent_execution.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AIC和AIV独立运行机制

## 功能介绍
AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不依赖消息驱动，开启双主模式能够提高Matmul计算性能。默认情况下，双主模式不开启，需要通过MatmulConfig中的enableMixDualMaster参数开启。
## 使用场景
算子中的矩阵计算和矢量计算相关代码独立运行，不依赖消息驱动时，可以开启双主模式，以提高Matmul计算性能。
## 约束说明
-   该功能仅支持Norm模板和MDL模板。
-   算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:1。
-   算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:2，且A矩阵和B矩阵同时开启IBSHARE参数。
-   同一算子中所有Matmul对象的该参数取值必须保持一致。
-   A、B、Bias矩阵只支持从Global Memory输入。
-   获取矩阵计算结果只支持调用IterateAll接口输出到GlobalTensor，即计算结果放置于Global Memory的地址，不能调用GetTensorC等接口获取结果。
