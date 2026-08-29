---
type: API
title: Round接口
description: 按元素四舍五入到最接近的整数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Round_interface/Round_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Round接口

按元素四舍五入到最接近的整数，并提供临时空间大小获取接口。

将输入的元素四舍五入到最接近的整数，计算公式如下： 举例如下： Round(3.5) = 4.0 Round(-3.4) = -3.0

本接口组包含 Round。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：只支持四舍五入到整数，不支持四舍五入到小数。如果该数恰好在两个整数中间，即小数部分为0.5，则“向偶数舍入”。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
