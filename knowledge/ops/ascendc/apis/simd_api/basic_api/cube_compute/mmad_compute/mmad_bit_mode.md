---
type: API
title: MmadBitMode
description: 优化的矩阵乘加接口，使用联合位域结构体MmadBitModeParams传参，适用于scalar流水成为性能瓶颈的场景。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/MmadBitMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# MmadBitMode

Mmad 的 BitMode 变体，使用 union 与 bit-field 结构体 MmadBitModeParams 传参，将多参数融合为单个入参，减少 scalar 计算开销。适用于 scalar 流水成为性能瓶颈的场景，支持基础 Mmad 和 MmadMx 计算功能。头文件 `basic_api/kernel_operator_mm_intf.h`。

原型含 Mmad 和 MmadMx 两个版本，各支持带/不带 bias。参数：dst（L0C/CO1，1024B 对齐）、fm（L0A/A2，fp4 512B 对齐/fp8 1024B 对齐）、filter（L0B/B2）、bias（BT/C2，64B 对齐）、mmadParams 为 MmadBitModeParams。可通过 Set 函数或直接对 config0 进行 bit 位运算修改参数。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Mmad](mmad.md)（`related`）：Mmad 的 BitMode 变体，使用 union 与 bit-field 结构体 MmadBitModeParams 传参，将多参数融合为单个入参，减少 scalar 计算开销。；Ascend C 矩阵乘加核心接口，实现 C=A×B+C。BitMode 保持 Mmad 的矩阵乘加核心语义，只改变参数编码并针对 scalar 流水瓶颈优化。
<!-- cannbot:related:end -->
