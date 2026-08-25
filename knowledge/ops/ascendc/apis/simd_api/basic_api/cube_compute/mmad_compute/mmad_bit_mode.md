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

- [Mmad辅助配置说明](../mmad_compute_aux_config/mmad_compute_aux_config.md)（`related`）：Mmad辅助配置说明说明Mmad 计算辅助配置接口集，包含 SetMMColumnMajor/SetMMRowMajor、SetHF32Mode、SetHF32TransMode 等。
- [LoadData（BitMode 2D矩阵搬运）](../cube_compute_load/load_data_2_d_bit_mode.md)（`same_topic`）：LoadData（BitMode 2D矩阵搬运）说明负责完成普通矩阵计算所需的2D格式数据的搬运，以大小为512字节的数据分形为单位进行搬运，支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（2D矩阵搬运V2）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load2DBitModeParam。
- [LoadData（BitMode卷积数据搬运）](../cube_compute_load/load_data_3_d_bit_mode.md)（`same_topic`）：LoadData（BitMode卷积数据搬运）说明LoadData（BitMode卷积数据搬运）用于完成image to column操作，将多维feature map转为二维矩阵。支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（卷积数据搬运）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load3DBitModeParam。
- [Mmad](mmad.md)（`same_topic`）：MmadBitMode 与 Mmad 执行同一 L0A×L0B 累加到 L0C 的矩阵乘加，BitMode 版本仅把配置参数压入位域；计算对象和结果合同一致。
- [SetFmatrixBitMode](../cube_load_aux_config/set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《MmadBitMode》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
<!-- cannbot:related:end -->
