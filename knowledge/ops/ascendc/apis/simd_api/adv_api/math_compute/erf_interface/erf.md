---
type: API
title: Erf
description: 按元素做误差函数计算，也称为高斯误差函数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Erf_interface/Erf.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Erf

按元素做误差函数计算（高斯误差函数，error function）。模板参数T支持half/float。

提供四种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，每种再区分源操作数全部参与计算（无calCount参数）和部分参与计算（带calCount参数）。临时空间大小通过GetErfMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可；config为ErfConfig类型，其中algo指定算法：PADE_APPROXIMATION（默认，高性能，帕德近似算法）或SUBSECTION_POLYNOMIAL_APPROXIMATION（高精度，分段多项式逼近）。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [ForeachErf A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_erf.md)（`related`）：焦点算子路线明确为“R-002 FLOAT32 直接 `Erf<float,false>`”，候选 API 的计算合同是“按元素做误差函数计算（高斯误差函数，error function）。”；该 primitive 是 ForeachErf FLOAT32 Device 路线的直接计算节点。
- [GetErfMaxMinTmpSize](get_erf_max_min_tmp_size.md)（`related`）：“host侧Tiling接口，用于获取Erf接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”与“临时空间大小通过GetErfMaxMinTmpSize获取。”是双方正文中的具体合同。Tiling 卡说明如何取得最大最小临时空间，Erf 计算卡明确把该接口作为 workspace 尺寸来源，二者组成 Host 估算到 Kernel 调用的前置链。
- [GetErfTmpBufferFactorSize](get_erf_tmp_buffer_factor_size.md)（`related`）：“推算公式：currentShapeSize = (currBuff - extraBuffer) / maxLiveNodeCount / typeSize，其中currBuff为可用临时空间（需去除输入输出空间）。”；“接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。”。factor 接口反推可计算元素规模，Erf 接口消费 sharedTmpBuffer 和 calCount，构成 Tiling 到计算调用的直接合同。
<!-- cannbot:related:end -->
