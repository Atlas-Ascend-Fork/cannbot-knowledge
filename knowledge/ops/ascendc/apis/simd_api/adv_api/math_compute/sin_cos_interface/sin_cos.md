---
type: API
title: SinCos
description: 按元素进行正弦计算和余弦计算，分别获得正弦和余弦的结果。 ! !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/SinCos_interface/SinCos.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# SinCos

按元素同时进行正弦和余弦计算，分别输出正弦结果（dst0）和余弦结果（dst1）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetSinCosMaxMinTmpSize获取。

模板参数config为SinCosConfig类型，含isReuseSource（预留，传false）。接口参数：dst0、dst1为两个输出操作数（正弦和余弦结果），TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。
