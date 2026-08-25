---
type: API
title: AddDeqRelu
description: 依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/AddDeqRelu.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# AddDeqRelu

复合矢量计算接口，按元素求和后反量化并 ReLU。计算公式 dst_i = relu((src0_i + src1_i) * deqScale)。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [AddRelu](add_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《AddRelu》明确“按元素求和，再进行Relu计算（结果和0对比取较大值）。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [AddReluCast](add_relu_cast.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《AddReluCast》明确“按元素求和，结果和0对比取较大值，并根据源操作数和目的操作数Tensor的数据类型进行精度转换。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [AscAddRelu](../../../c_api/vector_compute/asc_add_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《AscAddRelu》明确“按元素求和，再进行Relu计算（结果和0对比取较大值），并提供转换最终结果的数据类型的功能(s162s8、f322f16、f162s8)。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [CastDequant](cast_dequant.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《CastDequant》明确“对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [SetDeqScale](../type_conversion_aux_config/set_deq_scale.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《SetDeqScale》明确“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
<!-- cannbot:related:end -->
