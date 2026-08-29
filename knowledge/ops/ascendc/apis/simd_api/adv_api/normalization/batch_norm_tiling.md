---
type: API
title: BatchNorm Tiling
description: 获取BatchNorm kernel计算时所需的Tiling参数，包括通过GetBatchNormMaxMinTmpSize获取最大最小临时空间大小和GetBatchNormNDTilingInfo获取tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.normalization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/normalization/BatchNorm-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# BatchNorm Tiling

host侧Tiling接口，用于获取BatchNorm kernel计算所需的Tiling参数，分两步：通过GetBatchNormMaxMinTmpSize获取最大和最小临时空间大小（minValue保证功能正确，maxValue提升性能）；通过GetBatchNormNDTilingInfo获取kernel侧所需tiling参数（含切分信息、临时空间位置等），开发者无需关注tiling结构体细节，直接传入BatchNorm高阶API使用。

GetBatchNormMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetBatchNormNDTilingInfo参数：ascendcPlatform平台信息；srcShape(B,S,H)输入shape；typeSize数据类型字节数；isBasicBlock是否基本块；maxTmpSize可用临时空间；tiling输出BatchNormTiling结构体。约束：需保证B、S、H均大于0且S*H满足32B对齐。

<!-- cannbot:related:start -->
## 相关

- [BatchNorm](batch_norm.md)（`related`）：提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。Tiling参数通过BatchNorm Tiling获取。模板参数isReuseSource预留（传false）；isBasicBlock在满足基本块要求（originB为8的倍数，S*H为64的倍数且小于2048）时可设为true提升性能。；host侧Tiling接口，用于获取BatchNorm kernel计算所需的Tiling参数，分两步：通过GetBatchNormMaxMinTmpSize获取最大和最小临时空间大小（minValue保证功能正确，maxValue提升性能）；通过GetBatchNormNDTilingInfo获取kernel侧所需tiling参数（含切分信息、临时空间位置等），开发者无需关注tiling结构体细节，直接传入BatchNorm高阶API使用。；BatchNorm 明确消费 BatchNorm Tiling 生成的临时空间范围和切分参数，Tiling 页又规定如何产生这些参数，二者构成 Host 规划到 Kernel 调用的直接接口链。
<!-- cannbot:related:end -->
