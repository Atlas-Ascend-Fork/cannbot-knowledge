---
type: API
title: Xor
description: 按元素对两个输入数据执行按位异或运算。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Xor_interface/Xor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# Xor

按元素执行按位异或运算（同0异1，如3^5=6）。模板参数T支持int16_t/uint16_t。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetXorMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；src0Tensor、src1Tensor为两个输入源操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；仅支持ND格式输入；calCount需小于或等于src0Tensor/src1Tensor/dstTensor的元素范围；不带calCount参数时需保证src0Tensor和src1Tensor的shape大小相等；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetXorMaxMinTmpSize](get_xor_max_min_tmp_size.md)（`related`）：提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetXorMaxMinTmpSize获取。；host侧Tiling接口，用于获取Xor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；Xor 计算接口消费临时空间，Host Tiling 查询接口给出可传给 Kernel 的上下界，两者构成同一临时空间配置链。
<!-- cannbot:related:end -->
