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

<!-- cannbot:related:start -->
## 相关

- [GetFmaMaxMinTmpSize](get_fma_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Fma接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。接口内部涉及精度转换，临时空间大小通过GetFmaMaxMinTmpSize获取。。Host 查询提供 Fma 缓冲上下界，Kernel 执行重载消费显式或框架申请的临时空间，闭合 Tiling 到执行链。
- [GetFmaTmpBufferFactorSize](get_fma_tmp_buffer_factor_size.md)（`related`）：获取Fma接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。接口内部涉及精度转换，临时空间大小通过GetFmaMaxMinTmpSize获取。。factor 查询把固定临时空间换算为 Fma 单次元素上限，执行接口实际消费 sharedTmpBuffer 或框架缓冲。
<!-- cannbot:related:end -->
