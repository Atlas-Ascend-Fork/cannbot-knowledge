---
type: API
title: Sign接口
description: 按元素返回输入数据的符号（正数为1、负数为-1、零为0），并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sign_interface/Sign_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sign接口

按元素返回输入数据的符号（正数为1、负数为-1、零为0），并提供临时空间大小获取接口。

按元素执行Sign操作，Sign是指返回输入数据的符号，如果为0则返回0，如果为正数则返回1，如果为负数则返回-1。计算公式如下：

本接口组包含 Sign。

本接口属于高阶数学计算接口。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。；支持的数据类型

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetSignMaxMinTmpSize](get_sign_max_min_tmp_size.md)（`same_topic`）：GetSignMaxMinTmpSize说明在host侧获取Sign接口计算所需最大和最小临时空间大小，供Tiling参数选择。
- [GetSignTmpBufferFactorSize](get_sign_tmp_buffer_factor_size.md)（`same_topic`）：GetSignTmpBufferFactorSize：该因子接口只服务 Sign 的临时空间反推；Sign与接口页定义 kernel计算，MaxMinTmpSize给出另一种从shape正向估算的预算方式。 目标卡《Sign接口》补充：按元素返回输入数据的符号（正数为1、负数为-1、零为0），并提供临时空间大小获取接口。
- [Sign](sign.md)（`same_topic`）：Sign说明按元素返回输入数据的符号，零返回0，正数返回1，负数返回-1。
<!-- cannbot:related:end -->
