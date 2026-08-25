---
type: API
title: CastDequant
description: 对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.composite]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/composite_compute/CastDequant.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CastDequant

对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。

本接口用于设置DEQSCALE寄存器的值，DEQSCALE寄存器位宽为64bit，用于Vector计算单元上的量化计算，寄存器中存放的参数在不同场景下的含义不同：

本接口组包含 SetDeqScale, SetVectorMask, LocalTensor, 掩码操作, 高维切分。

本接口属于 UB 矢量计算复合算术接口，组合多个基础运算。

支持的数据类型为 uint64_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：offset量化参数，int16_t类型，只有前9位有效。；vdeq地址对齐约束参考地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AddDeqRelu](add_deq_relu.md)（`related`）：《AddDeqRelu》处理“依次计算按元素求和、结果进行deq量化后再进行relu计算（结果和0对比取较大值）。需与SetDeqScale接口配合使用。”。《CastDequant》明确“对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用。”，可直接用于核对AddDeqRelu 的加法、dequant scale、ReLU 与输出转换组合合同。
- [Dequantize](../../../adv_api/quantization/dequantize.md)（`related`）：Dequantize 与《CastDequant》的实质衔接是：Dequantize 的 workspace 查询、scale/offset 设置、替代反量化入口及量化逆过程共同约束数据类型恢复；所选故障卡直接验证 scale 与广播边界。
- [GetDequantizeMaxMinTmpSize](../../../adv_api/quantization/get_dequantize_max_min_tmp_size.md)（`related`）：GetDequantizeMaxMinTmpSize 与《CastDequant》的实质衔接是：GetDequantizeMaxMinTmpSize 与 factor 查询共同选择 kernel 临时空间，Dequantize/CastDequant 是消费端，Quantize 是逆过程，SetDequantType 决定输出模式。
- [SetDeqScale](../type_conversion_aux_config/set_deq_scale.md)（`related`）：CastDequant 在 int32 到 half 的反量化转换前必须由 SetDeqScale 配置量化尺度，二者是同一执行链的前置状态与计算。
- [AscSetDeqScale](../../../c_api/vector_compute/asc_set_deq_scale.md)（`same_topic`）：焦点处理C API DeqScale 与 dequant 计算及头文件约束；CastDequant正文说明“对输入做量化并进行精度转换，对输出结果的溢出采用饱和处理。需与SetDeqScale接口配合使用”。候选读取 DeqScale 完成 dequant，或给出 C API 可编译的包含与配置边界。
<!-- cannbot:related:end -->
