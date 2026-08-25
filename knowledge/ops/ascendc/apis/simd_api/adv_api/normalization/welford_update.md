---
type: API
title: WelfordUpdate
description: Welford算法的前处理接口，用于在线逐步计算均值和方差中间结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordFinalize实现等效计算LayerNorm。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/WelfordUpdate.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# WelfordUpdate

Welford算法的前处理接口，用于在线逐步计算均值和方差的中间结果。与WelfordFinalize配合使用，通过切分Reduce轴实现等效LayerNorm计算。分n次调用本接口，每次处理切分后的一块数据[1,k]，逐步累加计算前i块数据的均值和方差中间结果。第一次调用时Meant_0和M_0需为全0数据。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过WelfordUpdate Tiling获取。

接口参数：outputMean输出当前累加均值；outputM输出当前方差中间结果；inputX输入当前块数据；inputMean/inputM输入上一次的累加结果（第一次为全0）；sharedTmpBuffer临时缓存；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。
