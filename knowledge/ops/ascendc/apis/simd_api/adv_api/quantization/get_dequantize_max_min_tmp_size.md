---
type: API
title: GetDequantizeMaxMinTmpSize
description: 在host侧获取Dequantize接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetDequantizeMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# GetDequantizeMaxMinTmpSize

host侧Tiling接口，用于获取Dequantize接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetDequantizeMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与Dequantize接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [CastDequant](../../basic_api/memory_vector_compute/composite_compute/cast_dequant.md)（`related`）：GetDequantizeMaxMinTmpSize 与《CastDequant》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [SetDequantType](../cube_compute/matmul_tiling/set_dequant_type.md)（`related`）：GetDequantizeMaxMinTmpSize 与《SetDequantType》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [Dequantize](dequantize.md)（`same_topic`）：GetDequantizeMaxMinTmpSize 与《Dequantize》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [GetDequantizeTmpBufferFactorSize](get_dequantize_tmp_buffer_factor_size.md)（`same_topic`）：《GetDequantizeTmpBufferFactorSize》说明获取Dequantize接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。；《GetDequantizeMaxMinTmpSize》说明在host侧获取Dequantize接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。。二者在Dequantize的factor和最大/最小workspace查询为同一Kernel反推单次处理规模上存在可执行的直接衔接。
- [Quantize](quantize.md)（`same_topic`）：GetDequantizeMaxMinTmpSize 与《Quantize》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
<!-- cannbot:related:end -->
