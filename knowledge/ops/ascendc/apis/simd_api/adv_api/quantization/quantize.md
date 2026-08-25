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

<!-- cannbot:related:start -->
## 相关

- [Dequantize](dequantize.md)（`related`）：Dequantize 是将低精度结果恢复为高精度的逆向能力，常与 Quantize 构成压缩与恢复链。
- [GetQuantizeMaxMinTmpSize](get_quantize_max_min_tmp_size.md)（`related`）：Quantize 的 sharedTmpBuffer 大小需由 Host 侧 max/min 查询按 shape 和 dtype 预算。
- [AscendQuant](ascend_quant.md)（`same_topic`）：文档明确推荐用 Quantize 替代 AscendQuant；新接口保留量化任务并扩展 PER_GROUP 与舍入配置。
- [GetDequantizeMaxMinTmpSize](get_dequantize_max_min_tmp_size.md)（`same_topic`）：GetDequantizeMaxMinTmpSize 与《Quantize》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [GetQuantizeTmpBufferFactorSize](get_quantize_tmp_buffer_factor_size.md)（`same_topic`）：GetQuantizeTmpBufferFactorSize 与《Quantize》的实质衔接是：GetQuantizeTmpBufferFactorSize 用可用 UB 反推 Quantize 的单次元素数，GetQuantizeMaxMinTmpSize 给出另一种 Host 侧空间选择，Quantize kernel 是两类查询结果的直接消费方。
<!-- cannbot:related:end -->
