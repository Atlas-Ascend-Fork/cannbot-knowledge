---
type: API
title: Ceil接口
description: 提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Ceil_interface/Ceil_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Ceil接口

提供Ceil向上取整计算接口及其Tiling临时空间大小查询接口，包含Ceil、GetCeilMaxMinTmpSize等。

获取大于或等于x的最小的整数值，即向正无穷取整操作。计算公式如下： 举例如下： Ceil(3.9) = 4.0 Ceil (-3.9) = -3.0

本接口组包含 Ceil。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
