---
type: API
title: UnPad Tiling
description: 用于获取UnPad Tiling参数。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/UnPad-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# UnPad Tiling

host侧Tiling接口，用于获取UnPad kernel计算所需的Tiling参数，分两步：通过GetUnPadMaxMinTmpSize获取最大和最小临时空间大小；通过GetUnPadNDTilingInfo获取kernel侧所需tiling参数。

GetUnPadMaxMinTmpSize参数：ascendcPlatform平台信息；srcShape输入shape；typeSize数据类型字节数；isReuseSource预留传false；maxValue/minValue输出临时空间范围。

GetUnPadNDTilingInfo参数：ascendcPlatform平台信息；输入shape各维度；typeSize数据类型字节数；maxTmpSize可用临时空间；tiling输出UnPadTiling结构体。

<!-- cannbot:related:start -->
## 相关

- [Pad](pad.md)（`related`）：《UnPad Tiling》明确“用于获取UnPad Tiling参数。”；它与《Pad》的“对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。”在实际调用参数、数据流或结果校验上直接衔接。
- [Pad Tiling](pad_tiling.md)（`same_topic`）：《UnPad Tiling》处理“用于获取UnPad Tiling参数。”。《Pad Tiling》提供“用于获取Pad Tiling参数。”，其具体合同或探针直接接入UnPad 与其逆向 Pad 的宽度对齐和 Tiling 参数合同。
- [UnPad（张量变换）](un_pad.md)（`same_topic`）：《UnPad Tiling》处理“用于获取UnPad Tiling参数。”。《UnPad（张量变换）》提供“对height \ width的二维Tensor在width方向上进行unpad，如果Tensor的width非32B对齐，则不支持调用本接口unpad。本接口具体功能场景如下：Tensor的width已32B对齐，以half为例，如16\16，进行UnPad，变成16\15。”，其具体合同或探针直接接入UnPad 与其逆向 Pad 的宽度对齐和 Tiling 参数合同。
<!-- cannbot:related:end -->
