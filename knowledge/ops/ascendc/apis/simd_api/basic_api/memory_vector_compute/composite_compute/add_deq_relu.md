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

- [SetDeqScale](../type_conversion_aux_config/set_deq_scale.md)（`related`）：“复合矢量计算接口，按元素求和后反量化并 ReLU。计算公式 dst_i = relu((src0_i + src1_i) * deqScale)。支持 950/a2/a3。”与“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。”分别给出双端正文事实；AddDeqRelu 的反量化乘子来自 DEQSCALE 寄存器，SetDeqScale 负责配置该寄存器，形成调用前配置到复合矢量计算的直接参数依赖。
<!-- cannbot:related:end -->
