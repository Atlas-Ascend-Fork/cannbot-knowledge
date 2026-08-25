---
type: API
title: Quantize
description: 按元素做量化计算，将高精度数据转换为低精度数据，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种量化策略及舍入模式配置，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/Quantize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Quantize

按元素做量化计算，将高精度数据转换为低精度数据（如half/float量化为int8_t）。最多支持二维输入。推荐使用本接口替代AscendQuant，因其在PER_TENSOR/PER_CHANNEL场景扩展了舍入模式配置。仅Ascend 950PR/950DT支持。

支持四种量化策略：PER_TENSOR（scale/offset为标量）、PER_CHANNEL（scale/offset shape为[1,n]）、PER_TOKEN（scale/offset shape为[m,1]）、PER_GROUP（k方向每groupSize个元素共享一组参数）。每种策略均支持配置舍入模式。PER_GROUP根据输出类型分float4场景和b8场景。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetQuantizeMaxMinTmpSize获取。模板参数包含DstT目的类型、SrcT源类型、ScaleT/OffsetT系数类型。接口参数包含dstTensor输出、srcTensor输入、scale/offset量化系数、sharedTmpBuffer临时缓存、params参数信息（含量化策略、shape、groupSize、舍入模式等）。

约束：最多支持二维输入；遵循通用地址对齐约束。
