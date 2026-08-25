---
type: API
title: Cos接口
description: 提供Cos余弦计算接口及其Tiling临时空间大小查询接口，包含Cos、GetCosMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Cos_interface/Cos_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Cos接口

提供Cos余弦计算接口及其Tiling临时空间大小查询接口，包含Cos、GetCosMaxMinTmpSize等。

按元素做三角函数余弦运算，计算公式如下： Cos(x)的泰勒展开式为：

本接口组包含 Cos。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：对于Ascend 950PR/Ascend 950DT，模板参数config中使用多项式拟合算法POLYNOMIAL_APPROXIMATION时，必须保证输入源数据的值域在[-65504.0, 65504.0]范围内。；对于以下产品，输入源数据必须保持值域在[-65504.0, 65504.0]范围内。；Atlas A3 训练系列产品/Atlas A3 推理系列产品；Atlas A2 训练系列产品/Atlas A2 推理系列产品

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
