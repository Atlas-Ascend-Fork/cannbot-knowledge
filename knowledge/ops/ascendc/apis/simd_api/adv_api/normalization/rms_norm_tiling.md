---
type: API
title: RmsNorm Tiling
description: 获取RmsNorm kernel计算时所需的Tiling参数，包括通过GetRmsNormMaxMinTmpSize获取最大最小临时空间大小和GetRmsNormTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/RmsNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# RmsNorm Tiling

host侧Tiling接口，用于获取RmsNorm kernel计算所需的Tiling参数，分两步：通过GetRmsNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetRmsNormNDTilingInfo获取kernel侧所需tiling参数。

GetRmsNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetRmsNormNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度(B,S,H)；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出RmsNormTiling结构体。约束：需保证H满足32B对齐。

<!-- cannbot:related:start -->
## 相关

- [RmsNorm](rms_norm.md)（`related`）：“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过RmsNorm Tiling获取。模板参数isBasicBlock在满足基本块要求（H为64的倍数且小于2048，B*S为8的倍数）时可设为true提升性能。”与“host侧Tiling接口，用于获取RmsNorm kernel计算所需的Tiling参数，分两步：通过GetRmsNormMaxMinTmpSize获取最大和最小临时空间大小；通过GetRmsNormNDTilingInfo获取kernel侧所需tiling参数。”提供双方正文证据。RmsNorm kernel 明确消费 RmsNorm Tiling，tiling 卡给出先求临时空间再生成参数的两步 Host 流程。
<!-- cannbot:related:end -->
