---
type: API
title: RmsNorm
description: 实现对shape为[B,S,H]输入数据的RmsNorm归一化，其中γ为缩放系数，ε为防除零的权重系数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/RmsNorm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# RmsNorm

对shape为[B,S,H]的输入数据做RmsNorm归一化。计算公式：y = x / sqrt(mean(x²) + ε) * γ，其中γ为缩放系数，ε为防除零系数。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过RmsNorm Tiling获取。模板参数isBasicBlock在满足基本块要求（H为64的倍数且小于2048，B*S为8的倍数）时可设为true提升性能。

接口参数：dstLocal输出归一化结果（shape与srcLocal一致）；srcLocal输入（shape [B,S,H]，尾轴H需32B对齐）；gammaLocal缩放系数（shape [H]）；sharedTmpBuffer临时缓存；epsilon防除零系数；tiling切分信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：dstLocal和gammaLocal的Tensor空间不允许复用；仅支持ND格式；H轴非32B对齐时需补齐到32B对齐；遵循通用地址对齐约束。
