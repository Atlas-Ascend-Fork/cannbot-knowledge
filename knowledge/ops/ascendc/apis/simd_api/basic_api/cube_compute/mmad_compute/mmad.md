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
