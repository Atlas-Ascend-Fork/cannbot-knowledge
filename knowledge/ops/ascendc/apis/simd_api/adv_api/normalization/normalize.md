---
type: API
title: Normalize
description: 在已知均值和方差的情况下，计算shape为[A,R]输入数据的标准差倒数rstd和归一化结果y，其中γ为缩放系数、β为平移系数、ε为防除零系数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/Normalize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# Normalize

已知均值和方差，计算shape为[A,R]的输入数据的标准差倒数rstd和归一化结果y。计算公式：rstd = 1/sqrt(Var+ε)，y = γ*(x-E)*rstd + β。其中E和Var为输入在R轴的均值和方差，γ为缩放系数，β为平移系数。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过Normalize Tiling获取。模板参数isReuseSource预留（传false）；config为NormalizeConfig类型。

接口参数：output归一化结果；outputRstd标准差倒数；inputMean/inputVariance输入均值和方差（float类型）；inputX输入数据；gamma/beta缩放平移系数；sharedTmpBuffer临时缓存；epsilon防除零系数；para参数信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Normalize Tiling](normalize_tiling.md)（`related`）：Tiling参数通过Normalize Tiling获取。；host侧Tiling接口，用于获取Normalize kernel计算所需的Tiling参数，分两步：通过GetNormalizeMaxMinTmpSize获取最大和最小临时空间大小；通过GetNormalizeNDTilingInfo获取kernel侧所需tiling参数。。Normalize Kernel 明确消费 Normalize Tiling 生成的参数，右侧又完整描述临时空间和 ND Tiling 两步准备；这是 Host 参数生产到 Kernel 计算消费的互补任务链。
<!-- cannbot:related:end -->
