---
type: API
title: AscendQuant
description: 按元素做量化计算，将half/float数据类型量化为int8_t数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN等量化策略。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/AscendQuant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# AscendQuant

按元素做量化计算（如half/float量化为int8_t），计算公式：dst = round(cast((src + offset) * scale))，其中round为四舍六入五成双取整，cast为舍入模式。支持950PR/950DT、A3、A2训练/推理、推理AI Core、训练系列、Kirin X90/9030。推荐使用Quantize替代本接口。

支持四种量化策略：PER_TENSOR（scale/offset为标量shape [1]）、PER_CHANNEL（scale/offset shape为[n]）、PER_TOKEN（scale/offset shape为[m,1]，offset可选）、PER_GROUP（k方向每groupSize个元素共享一组参数，offset可选）。PER_GROUP根据输出类型分float4场景和b8场景。

提供多种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请，支持不同量化场景和舍入模式配置。临时空间大小通过GetAscendQuantMaxMinTmpSize获取。接口参数包含dstTensor输出、srcTensor输入、scale/offset量化系数、sharedTmpBuffer临时缓存、params参数信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；遵循通用地址对齐约束。
