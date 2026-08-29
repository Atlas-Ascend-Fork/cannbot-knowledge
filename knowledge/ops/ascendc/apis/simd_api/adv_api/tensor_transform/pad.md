---
type: API
title: Pad
description: 对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Pad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Pad

对height*width的二维Tensor在width方向上pad到32B对齐。若width已32B对齐且全部为有效数据则不支持调用。支持两种场景：width非32B对齐时补齐到32B对齐；width已32B对齐但有冗余数据时，可将冗余位置填充为设定值。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过Pad Tiling获取。接口参数：dstTensor输出pad后结果；srcTensor输入数据；sharedTmpBuffer临时缓存；padParams含height、width、padNum等信息。

约束：仅支持二维输入；width需补齐到32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Pad Tiling](pad_tiling.md)（`related`）：提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过Pad Tiling获取。；host侧Tiling接口，用于获取Pad kernel计算所需的Tiling参数，分两步：通过GetPadMaxMinTmpSize获取最大和最小临时空间大小；通过GetPadNDTilingInfo获取kernel侧所需tiling参数。。Pad Kernel 明确从 Pad Tiling 获取参数，Host Tiling 页给出先预算临时空间再生成 PadTiling 结构体的两步调用链。
<!-- cannbot:related:end -->
