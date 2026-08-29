---
type: API
title: Mmad
description: 矩阵乘加核心计算接口，封装昇腾NPU硬件矩阵乘加能力，实现C=A*B+C，广泛用于全连接层、卷积层等算子开发。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Mmad

Ascend C 矩阵乘加核心接口，实现 C=A×B+C。头文件 `basic_api/kernel_operator_mm_intf.h`。矩阵 A 位于 L0A Buffer（M×K，950 格式 Nz/a2/a3 格式 Zz），矩阵 B 位于 L0B Buffer（K×N，Zn），结果 C 位于 L0C Buffer（M×N，Nz），可选用 Bias（1×N）初始化。

两个原型：不带 bias 和带 bias。参数：dst 为 LocalTensor（L0C/CO1，1024B 对齐）；fm 为左矩阵 A（L0A/A2，512B 对齐）；filter 为右矩阵 B（L0B/B2，512B 对齐）；bias 为偏置矩阵（BT/C2，64B 对齐）；mmadParams 为 MmadParams 结构体，含 mSize/kSize/nSize 等矩阵维度参数。数据类型支持 half/int8_t/int4_t 等，具体组合因型号而异。

不传 bias 原型支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Atlas 训练/Kirin X90/9030；传 bias 原型不支持 Atlas 推理 AI Core/Atlas 训练/Kirin 9030。不支持 Vector Core。

<!-- cannbot:related:start -->
## 相关

- [Conv2D（废弃）](conv2_d_deprecated.md)（`related`）：该接口已废弃，将在后续版本移除，请勿使用。计算输入张量和权重张量的 2D 卷积，输出结果张量，多用于图像识别中的特征提取。；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。头文件 `basic_api/kernel_operator_mm_intf.h`。矩阵 A 位于 L0A Buffer（M×K，950 格式 Nz/a2/a3 格式 Zz），矩阵 B 位于 L0B Buffer（K×N，Zn），结果 C 位于 L0C Buffer（M×N，Nz），可选用 Bias（1×N）初始化。；焦点明确要求用 Mmad 替代废弃 Conv2D，目标补齐替代接口的矩阵与 L0 缓冲合同。
- [Gemm（废弃）](gemm_deprecated.md)（`related`）：请使用 Mmad 等接口替代。；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。废弃 Gemm 卡给出明确替代方向，Mmad 卡提供替代接口的计算语义、输入 Buffer 与对齐契约。
- [K方向对齐约束](../mmad_compute_key_features/k_direction_alignment_constraint.md)（`related`）：通过 MmadParams.kDirectionAlign 控制 float 数据类型时 L0A/L0B Buffer 矩阵 K 方向对齐方式。；mmadParams 为 MmadParams 结构体，含 mSize/kSize/nSize 等矩阵维度参数。。对齐页定义 MmadParams 中 kDirectionAlign 的布局契约，核心 Mmad 页说明该参数结构体正由矩阵乘加接口消费。
- [MmadBitMode](mmad_bit_mode.md)（`related`）：Mmad 的 BitMode 变体，使用 union 与 bit-field 结构体 MmadBitModeParams 传参，将多参数融合为单个入参，减少 scalar 计算开销。；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。BitMode 保持 Mmad 的矩阵乘加核心语义，只改变参数编码并针对 scalar 流水瓶颈优化。
- [Mmad](../../cube_compute_tensor_api/mmad_compute/mmad.md)（`same_topic`）：完成L0A Buffer上左矩阵A和L0B Buffer上右矩阵B的矩阵乘加，结果写入L0C Buffer上结果矩阵C；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。两端均定义 L0A/L0B 输入、L0C 输出的矩阵乘加操作，分别是 950 Tensor API 与基础 API 形态。
<!-- cannbot:related:end -->
