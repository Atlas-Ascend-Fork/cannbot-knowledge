---
type: API
title: 基础API随路量化
description: 随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global
  Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_store_key_features/quant_pre.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 基础API随路量化

随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global

本接口属于 Cube 矩阵计算接口。

约束：tensor量化参数张量应位于L1 Buffer，元素类型为uint64_t，地址要求32字节对齐。；量化参数不能为inf、nan或非规格化数。该约束属于硬件约束，接口不单独检查参数值。；RoundMode::HYBRID仅在源类型为float、目的类型为hifloat8_t的量化输出场景支持。；不传入quant时，仅支持不量化输出或float到half/bfloat16_t的直接cast输出。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Copy](../cube_compute_store/copy_l0_c_to_gm.md)（`related`）：《Copy》明确“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”；它与《基础API随路量化》的“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopyL0CToGM](../../cube_compute/cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：《DataCopyL0CToGM》明确“将L0C Buffer中的矩阵计算结果搬运至Global Memory，支持随路量化、ReLU激活和NZ2ND格式转换。”；它与《基础API随路量化》的“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetFixPipeConfig](../../cube_compute/cube_store_aux_config/set_fix_pipe_config.md)（`related`）：SetFixPipeConfig 与《基础API随路量化》的实质衔接是：SetFixPipeConfig 将 tensor 量化参数放入 Fixpipe Buffer，供 L0C 到 GM/L1 的 DataCopy/Fixpipe 搬出消费；PreQuant、Addr、ClipReLU 和 UnitFlag 配置分别控制标量前量化、后处理地址、激活与细粒度同步。
- [AccompanyingQuantization](../../cube_compute/cube_store_key_features/accompanying_quantization.md)（`same_topic`）：“AccompanyingQuantization”处理矩阵计算搬出过程中支持随路cast和quant能力，包括Scalar和Tensor两种量化模式，支持多种量化类型。；“基础API随路量化”明确随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。。实质衔接：随路量化发生在 L0C 搬出路径，量化模式决定 scalar/Tensor 参数应写入寄存器还是 Fixpipe Buffer，并由对应搬出和配置接口落地。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《基础API随路量化》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [Int8 Channel Merge](../../cube_compute/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；基础API随路量化正文说明“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
<!-- cannbot:related:end -->
