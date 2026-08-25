---
type: API
title: GetAscendQuantMaxMinTmpSize
description: 在host侧获取AscendQuant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetAscendQuantMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetAscendQuantMaxMinTmpSize

host侧Tiling接口，用于获取AscendQuant接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetAscendQuantMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与AscendQuant接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [量化操作](quantization.md)（`related`）：《GetAscendQuantMaxMinTmpSize》说明在host侧获取AscendQuant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。；《量化操作》说明量化操作接口导航页，涵盖AscendQuant、AscendDequant、AscendAntiQuant及Quantize系列量化与反量化接口。。二者在AscendQuant的Host侧workspace上界/下界必须与该量化Kernel及factor查询匹配上存在可执行的直接衔接。
- [AscendQuant](ascend_quant.md)（`same_topic`）：该接口给出 AscendQuant 可用 workspace 上下界，是调用旧接口前的直接 Tiling 配套。
- [GetAscendQuantTmpBufferFactorSize](get_ascend_quant_tmp_buffer_factor_size.md)（`same_topic`）：《GetAscendQuantMaxMinTmpSize》说明在host侧获取AscendQuant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。；《GetAscendQuantTmpBufferFactorSize》说明获取AscendQuant接口的maxLiveNodeCount和extraBuf，在固定空间大小下推算算子单次最大计算元素数量。。二者在AscendQuant的Host侧workspace上界/下界必须与该量化Kernel及factor查询匹配上存在可执行的直接衔接。
<!-- cannbot:related:end -->
