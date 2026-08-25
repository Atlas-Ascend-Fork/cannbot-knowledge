---
type: API
title: Erfc接口
description: 按元素计算x的互补误差函数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erfc_interface/Erfc_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erfc接口

按元素计算x的互补误差函数，并提供临时空间大小获取接口。

返回输入x的互补误差函数结果，积分区间为x到无穷大。原始的理论计算公式如下： 由于Erfc函数没有初等函数表达方式，一般通过函数逼近的方式计算，近似计算公式如下所示： 其中， R(z) = (((((((z * R0 + R1) * z + R2) * z + R3) * z + R4) * z + R5) * z + R6) * z + R7) * z + R8是关于z的8次多项式； S(z) = ((((z + S1) * z + S2) * z + S3) * z + S4) * z + S5是关于z的4次多项式。

本接口组包含 Erfc。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入源数据需保持值域在[-inf, inf]。若输入不在范围内，输出结果无效。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
