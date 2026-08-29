---
type: API
title: AscCopyL0c2Gm
description: 将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_copy_l0c2gm/asc_copy_l0c2gm.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# AscCopyL0c2Gm

将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。

矩阵计算完成后，对结果进行量化处理，之后将处理结果搬运到GM中。量化模式共分为9种，分别为： - NoQuant：不开启量化功能。 - F322F16：float量化成half。量化结果不支持INF_NAN模式。 - F322BF16：float量化成bfloat16_t。量化结果不支持INF_NAN模式。 - DEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。 - VDEQF16：int32_t量化成half。量化结果不支持INF_NAN模式。 - QF322B8_PRE：float量化成uint8_t/int8_t。scalar量化。 - VQF322B8_PRE：float量化成uint8_t/int8_t。矢量量化。 - REQ8：int32_t量化成uint8_t/int8_t。scalar量化。 - VREQ8：int32_t量化成uint8_t/i

本接口组包含 asc_copy_l0c2gm_arch_2201, asc_copy_l0c2gm_arch_3510。

约束：各存储单元的空间大小和对齐要求请参考存储单元说明。；操作数地址重叠约束请参考通用地址重叠约束。

支持的硬件型号：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscSetL0c2gmLreluAlpha](../asc_set_l0c2gm_lrelu_alpha.md)（`related`）：用于设置asc_copy_l0c2l1或asc_copy_l0c2gm接口计算过程中使用的Leaky ReLU alpha值。该值只支持half和float两种数据类型。；将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。；alpha 设置接口为 asc_copy_l0c2gm 的随路 Leaky ReLU 提供参数，搬运接口则执行含激活能力的 L0C 到 GM 数据路径。
- [AscSetL0cCopyParams](../asc_set_l0c_copy_params.md)（`related`）：DataCopy从L0C Buffer搬运到Global Memory或L1 Buffer过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。；将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。；配置接口为 L0C 搬运的 NZ→ND 随路格式转换设置参数，asc_copy_l0c2gm 是执行同一 L0C→GM 格式转换搬运的接口族。
- [AscSetL0cCopyPrequant](../asc_set_l0c_copy_prequant.md)（`related`）：数据搬运过程中进行随路量化时，通过调用该接口设置量化流程中的标量量化参数。；将矩阵计算结果从L0C Buffer搬运至GM，支持随路量化、ReLU、格式转换等能力，包含不同架构版本实现。；AscSetL0CCopyPreQuant 配置搬运随路量化使用的标量参数，AscCopyL0c2Gm 则在 L0C 到 GM 搬运中执行该随路量化能力，前者直接支撑后者的量化路径。
<!-- cannbot:related:end -->
