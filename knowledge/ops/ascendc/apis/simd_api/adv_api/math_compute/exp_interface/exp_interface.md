---
type: API
title: Exp接口
description: 按元素取自然指数，可选泰勒展开计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Exp_interface/Exp_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Exp接口

按元素取自然指数，可选泰勒展开计算，并提供临时空间大小获取接口。

按元素取自然指数，用户可以选择是否使用泰勒展开公式进行计算，计算公式如下： - 设置泰勒展开项数为0，即不使用泰勒展开公式进行计算，公式如下： - 设置泰勒展开项数不为0，即使用泰勒展开公式进行计算，公式如下： xA i 代表源操作数的整数部分，该值通过floor(x)获取。xB i 代表源操作数的小数部分。 泰勒展开公式如下：

本接口组包含 Exp。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
