---
type: API
title: SetDeqScale
description: 设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.type_conversion]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/type_conversion_aux_config/SetDeqScale.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetDeqScale

设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。

依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。计算公式如下： Deq的计算公式如下，采用RINT舍入方式，scale需要通过SetDeqScale进行设置： 其中Relu的计算公式如下：

本接口组包含 AddDeqRelu, Cast, CastDequant。

本接口属于 UB 矢量计算类型转换接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；操作数地址重叠约束请参考通用地址重叠约束。；当参数count或repeatTime取值为0时，该接口的行为如下：；针对如下型号，该接口不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AddDeqRelu](../composite_compute/add_deq_relu.md)（`related`）：“复合矢量计算接口，按元素求和后反量化并 ReLU。计算公式 dst_i = relu((src0_i + src1_i) * deqScale)。支持 950/a2/a3。”与“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。”分别给出双端正文事实；AddDeqRelu 的反量化乘子来自 DEQSCALE 寄存器，SetDeqScale 负责配置该寄存器，形成调用前配置到复合矢量计算的直接参数依赖。
- [CastDequant](../composite_compute/cast_dequant.md)（`related`）：“对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。”；“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。”。SetDeqScale 写入 CastDequant 计算前必须存在的 DEQSCALE 配置。
<!-- cannbot:related:end -->
