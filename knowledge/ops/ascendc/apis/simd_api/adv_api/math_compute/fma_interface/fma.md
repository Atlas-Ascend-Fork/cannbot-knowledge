---
type: API
title: Fma
description: 按元素计算两个输入相乘后与第三个输入相加的结果
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Fma_interface/Fma.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Fma

按元素计算两个输入相乘后与第三个输入相加的结果（dst = src0 * src1 + src2）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。接口内部涉及精度转换，临时空间大小通过GetFmaMaxMinTmpSize获取。

模板参数config为FmaConfig类型，含isReuseSource（预留，传false）。接口参数：dst为输出操作数；src0、src1、src2为三个输入源操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。
