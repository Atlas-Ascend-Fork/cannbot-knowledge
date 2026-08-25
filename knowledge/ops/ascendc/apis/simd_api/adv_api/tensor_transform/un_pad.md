---
type: API
title: UnPad（张量变换）
description: 对height \ width的二维Tensor在width方向上进行unpad，如果Tensor的width非32B对齐，则不支持调用本接口unpad。本接口具体功能场景如下：Tensor的width已32B对齐，以half为例，如16\16，进行UnPad，变成16\15。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/UnPad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# UnPad

对height*width的二维Tensor在width方向上进行unpad（去除padding）。若width非32B对齐则不支持调用。例如16*16的Tensor进行UnPad变为16*15。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。Tiling参数通过UnPad Tiling获取。接口参数：dstTensor输出unpad后结果；srcTensor输入数据；sharedTmpBuffer临时缓存；unPadParams含height、width、unpadNum等信息。

约束：仅支持二维输入；width需已32B对齐；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Pad](pad.md)（`related`）：《UnPad（张量变换）》明确“对height \ width的二维Tensor在width方向上进行unpad，如果Tensor的width非32B对齐，则不支持调用本接口unpad。本接口具体功能场景如下：Tensor的width已32B对齐，以half为例，如16\16，进行UnPad，变成16\15。”；它与《Pad》的“对二维Tensor在width方向上pad到32B对齐，或对已对齐但含冗余数据的列填充设定值。”在实际调用参数、数据流或结果校验上直接衔接。
- [UnPad Tiling](un_pad_tiling.md)（`same_topic`）：《UnPad Tiling》处理“用于获取UnPad Tiling参数。”。《UnPad（张量变换）》提供“对height \ width的二维Tensor在width方向上进行unpad，如果Tensor的width非32B对齐，则不支持调用本接口unpad。本接口具体功能场景如下：Tensor的width已32B对齐，以half为例，如16\16，进行UnPad，变成16\15。”，其具体合同或探针直接接入UnPad 与其逆向 Pad 的宽度对齐和 Tiling 参数合同。
<!-- cannbot:related:end -->
