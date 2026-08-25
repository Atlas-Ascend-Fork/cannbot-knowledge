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

- [UnPad Tiling](un_pad_tiling.md)（`related`）：《UnPad Tiling》明确“用于获取UnPad Tiling参数。”；它与《Pad》的“对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。”在实际调用参数、数据流或结果校验上直接衔接。
- [UnPad（张量变换）](un_pad.md)（`related`）：《UnPad（张量变换）》明确“对height \ width的二维Tensor在width方向上进行unpad，如果Tensor的width非32B对齐，则不支持调用本接口unpad。本接口具体功能场景如下：Tensor的width已32B对齐，以half为例，如16\16，进行UnPad，变成16\15。”；它与《Pad》的“对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。”在实际调用参数、数据流或结果校验上直接衔接。
- [Pad Tiling](pad_tiling.md)（`same_topic`）：《Pad Tiling》的任务是“用于获取Pad Tiling参数。”。《Pad》具体提供“对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。”，它直接用于Pad Kernel 所需 Tiling 参数。
<!-- cannbot:related:end -->
