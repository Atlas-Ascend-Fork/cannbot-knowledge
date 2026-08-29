---
type: API
title: Sigmoid接口
description: 提供Sigmoid激活函数接口及GetSigmoidMaxMinTmpSize等Tiling临时空间大小查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Sigmoid_interface/Sigmoid_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sigmoid接口

提供 Sigmoid 激活函数及 GetSigmoidMaxMinTmpSize 临时空间查询接口。Sigmoid 按元素做逻辑回归计算，输出 1/(1+e^(-x))。

接口为模板函数，支持 half、float 数据类型，`isReuseSource` 参数预留。通过 `calCount` 可指定参与计算的元素个数，也可省略表示全部参与。临时空间支持 `sharedTmpBuffer` 传入和框架申请两种方式，大小通过 GetSigmoidMaxMinTmpSize 获取。源操作数数据类型需与目的操作数一致，操作数地址需满足通用对齐约束。
