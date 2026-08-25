---
type: API
title: GetAscendDequantMaxMinTmpSize
description: 在host侧获取AscendDequant接口计算所需的最大和最小临时空间大小，用于选择合适的空间大小作为Tiling参数传递到kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.quantization]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/quantization/GetAscendDequantMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# GetAscendDequantMaxMinTmpSize

host侧Tiling接口，用于获取AscendDequant接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetAscendDequantMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape；typeSize为数据类型字节数（half传2）；isReuseSource与AscendDequant接口保持一致；maxValue输出最大临时空间大小（超出不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间）；minValue输出最小临时空间大小（实际预留不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [AscendDequant](ascend_dequant.md)（`related`）：AscendDequant 是该 Host workspace 查询所服务的 Kernel 计算接口，isReuseSource 和 typeSize 必须在两侧一致。
- [GetAscendDequantTmpBufferFactorSize](get_ascend_dequant_tmp_buffer_factor_size.md)（`same_topic`）：GetAscendDequantTmpBufferFactorSize 与《GetAscendDequantMaxMinTmpSize》的实质衔接是：factor 查询与 GetAscendDequantMaxMinTmpSize 共同换算临时空间和单次元素数，AscendDequant 是结果消费方，SetDequantType 控制输出模式。
<!-- cannbot:related:end -->
