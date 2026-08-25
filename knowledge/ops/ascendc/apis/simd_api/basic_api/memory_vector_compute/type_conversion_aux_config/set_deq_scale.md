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

- [AddDeqRelu](../composite_compute/add_deq_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《SetDeqScale》明确“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [CastDequant](../composite_compute/cast_dequant.md)（`related`）：CastDequant 在 int32 到 half 的反量化转换前必须由 SetDeqScale 配置量化尺度，二者是同一执行链的前置状态与计算。
- [AscDeqInt322half](../../../c_api/vector_compute/asc_deq_int322half.md)（`same_topic`）：AscDeqInt322half 需要预先设置 dequant scale；该辅助接口定义同一反量化比例契约。
- [AscSetDeqScale](../../../c_api/vector_compute/asc_set_deq_scale.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；SetDeqScale正文说明“设置DEQSCALE寄存器的值，用于Vector计算单元上的量化计算，支持不同场景的量化参数配置”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
- [AscVdeqInt162b8](../../../c_api/vector_compute/asc_vdeq_int162b8.md)（`same_topic`）：AscVdeqInt162b8 与《SetDeqScale》的实质衔接是：AscVdeqInt162b8 调用前必须设置 deq scale；C/basic SetDeqScale 是直接前置契约，AscDeqInt162b8和头文件故障卡用于区分相关符号及正确包含方式。
- [类型转换辅助配置接口](type_conversion_aux_config.md)（`same_topic`）：类型转换辅助配置接口 与《SetDeqScale》的实质衔接是：类型转换辅助配置以 deq scale/rounding 驱动 Cast/Truncate 与精度转换。
<!-- cannbot:related:end -->
