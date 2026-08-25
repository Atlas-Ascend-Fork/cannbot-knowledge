---
type: API
title: Dequantize
description: 按元素做反量化计算，将int32_t数据类型反量化为half/float等数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种反量化策略，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/Dequantize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Dequantize

按元素做反量化计算（如int32_t反量化为half/float），将高精度整数类型转换为浮点类型。最多支持二维输入。推荐使用本接口替代AscendDequant。仅Ascend 950PR/950DT支持。

支持四种反量化策略：PER_TENSOR（scale为标量）、PER_CHANNEL（scale shape为[1,n]）、PER_TOKEN（scale shape为[m,1]）、PER_GROUP（k方向每groupSize个元素共享一组scale）。计算公式：dst = src * scale + offset（offset可选）。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetDequantizeMaxMinTmpSize获取。模板参数包含DstT目的类型、SrcT源类型、ScaleT/OffsetT系数类型。接口参数包含dstTensor输出、srcTensor输入、scale/offset反量化系数、sharedTmpBuffer临时缓存、params参数信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；遵循通用地址对齐约束。
