---
type: API
title: Tan接口
description: 按元素做正切函数计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Tan_interface/Tan_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Tan接口

按元素做正切函数计算，并提供临时空间大小获取接口。

按元素做正切函数计算，计算公式如下： Tan(x)的泰勒展开式为： 其中B 2n 是伯努利数。

本接口组包含 Tan。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：输入数据限制在(-65504.0, 65504.0)范围内。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetTanMaxMinTmpSize](get_tan_max_min_tmp_size.md)（`same_topic`）：临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。；host侧Tiling接口，用于获取Tan接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。前者声明 Tan 的临时空间获取方式，后者给出对应 Host 查询入口，两者闭合 sharedTmpBuffer 的准备步骤。
<!-- cannbot:related:end -->
