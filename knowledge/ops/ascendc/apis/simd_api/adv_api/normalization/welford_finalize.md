---
type: API
title: WelfordFinalize
description: Welford算法的后处理接口，用于在线计算均值和方差的最终结果。LayerNorm中Reduce轴较大时可切分Reduce轴，联合WelfordUpdate实现等效计算LayerNorm。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/WelfordFinalize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# WelfordFinalize

Welford算法的后处理接口，用于在线计算均值和方差的最终结果。与WelfordUpdate配合使用，通过切分Reduce轴实现等效LayerNorm计算。Welford方法无需存储所有样本即可逐步计算均值和方差，适合处理海量数据且只需一次遍历。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过WelfordFinalize Tiling获取。接口接收WelfordUpdate输出的均值和方差中间结果，计算最终的均值和方差。支持带尾块（带counts参数）和不带尾块两种场景，方差计算支持系数修正和非修正模式。

接口参数：outputMean输出最终均值；outputVariance输出最终方差；inputMean/inputVariance输入WelfordUpdate的中间结果；sharedTmpBuffer临时缓存；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：仅支持ND格式；遵循通用地址对齐约束。
