---
type: API
title: Pad Tiling
description: 用于获取Pad Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Pad-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Pad Tiling

host侧Tiling接口，用于获取Pad kernel计算所需的Tiling参数，分两步：通过GetPadMaxMinTmpSize获取最大和最小临时空间大小；通过GetPadNDTilingInfo获取kernel侧所需tiling参数。

GetPadMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetPadNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出PadTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [Pad](pad.md)（`related`）：提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过Pad Tiling获取。；host侧Tiling接口，用于获取Pad kernel计算所需的Tiling参数，分两步：通过GetPadMaxMinTmpSize获取最大和最小临时空间大小；通过GetPadNDTilingInfo获取kernel侧所需tiling参数。。Pad Kernel 明确从 Pad Tiling 获取参数，Host Tiling 页给出先预算临时空间再生成 PadTiling 结构体的两步调用链。
<!-- cannbot:related:end -->
