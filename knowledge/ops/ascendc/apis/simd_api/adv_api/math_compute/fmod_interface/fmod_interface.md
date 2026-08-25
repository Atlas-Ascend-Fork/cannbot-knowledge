---
type: API
title: Fmod接口
description: 按元素计算两个浮点数相除后的余数，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fmod_interface/Fmod_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Fmod接口

按元素计算两个浮点数相除后的余数，并提供临时空间大小获取接口。

按元素计算两个浮点数a, b相除后的余数。计算公式如下： 其中，Trunc为向零取整操作。举例如下： Fmod(2.0, 1.5) = 0.5 Fmod(-3.0, 1.1) = -0.8

本接口组包含 Fmod。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内。；源操作数src0Tensor与src1Tensor的数据长度必须保持一致。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Fmodf](../../../../simt_api/math_functions/float_math_functions/fmodf.md)（`related`）：Fmodf 与 SIMD 高阶 Fmod 都计算截断除法语义的浮点余数，分别适合 SIMT 标量线程和 LocalTensor 向量路径。
- [GetFmodTmpBufferFactorSize](get_fmod_tmp_buffer_factor_size.md)（`related`）：GetFmodTmpBufferFactorSize 与《Fmod接口》的实质衔接是：Fmod 的 factor-size、max/min 临时空间、kernel 接口和标量实现共同决定固定 UB 下单次元素数及除零保护。
- [GetFmodMaxMinTmpSize](get_fmod_max_min_tmp_size.md)（`same_topic`）：GetFmodMaxMinTmpSize 的核心契约是“在host侧获取Fmod接口预留或申请临时空间的最大和最小值，用于Tiling参数传递”；Fmod接口 补充“按元素计算两个浮点数相除后的余数，并提供临时空间大小获取接口”。
<!-- cannbot:related:end -->
