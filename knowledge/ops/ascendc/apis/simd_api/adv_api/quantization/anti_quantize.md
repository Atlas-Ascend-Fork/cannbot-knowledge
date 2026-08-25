---
type: API
title: AntiQuantize
description: 按元素做伪量化计算，将int8_t等低精度数据类型伪量化为half等高精度数据类型，支持PER_TENSOR、PER_CHANNEL、PER_TOKEN、PER_GROUP四种量化策略，最多支持二维输入。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/AntiQuantize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# AntiQuantize

按元素做伪量化计算（如int8_t伪量化为half），将低精度数据类型转换为高精度数据类型。最多支持二维输入。推荐使用本接口替代AscendAntiQuant，因其在不同量化场景下形式更统一。仅Ascend 950PR/950DT支持。

支持四种伪量化策略：PER_TENSOR（按张量，scale/offset为标量）、PER_CHANNEL（按通道，scale/offset shape为[1,n]）、PER_TOKEN（按token，scale/offset shape为[m,1]）、PER_GROUP（按组，k方向每groupSize个元素共享一组参数）。PER_GROUP根据输入类型分float4场景（fp4x2_e2m1_t/fp4x2_e1m2_t）和b8场景（int8_t/hifloat8_t/fp8_e5m2_t/fp8_e4m3fn_t）。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetAntiQuantizeMaxMinTmpSize获取。接口参数包含dstTensor输出、srcTensor输入、scale/offset量化系数、sharedTmpBuffer临时缓存、params参数信息（含量化策略、shape、groupSize等）。TPosition支持VECIN/VECCALC/VECOUT。

约束：最多支持二维输入；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [AscendAntiQuant](ascend_anti_quant.md)（`same_topic`）：AscendAntiQuant 与《AntiQuantize》的实质衔接是：AscendAntiQuant 依赖两种空间查询，generic AntiQuant 是同任务入口，AscendQuant 是逆过程；scale 错配卡直接约束分组反量化。
- [GetAntiQuantizeMaxMinTmpSize](get_anti_quantize_max_min_tmp_size.md)（`same_topic`）：GetAntiQuantizeMaxMinTmpSize 与《AntiQuantize》的实质衔接是：GetAntiQuantizeMaxMinTmpSize 给 AntiQuantize 划定可用临时空间范围，factor 查询在固定空间下反推单次处理元素数。
- [GetAntiQuantizeTmpBufferFactorSize](get_anti_quantize_tmp_buffer_factor_size.md)（`same_topic`）：factor-size 依据元素数计算 AntiQuantize 临时空间，与 max/min 查询构成可选的两套 Tiling 配置方法。
<!-- cannbot:related:end -->
