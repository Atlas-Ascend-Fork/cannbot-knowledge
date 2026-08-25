---
type: API
title: Copy
description: 将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_store/Copy_L0CToGM.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# Copy（L0C到GM数据搬运）

通过统一Copy接口将L0C Buffer数据搬运到Global Memory，用于矩阵计算结果输出。搬运参数由Tensor Layout自动推导。仅Ascend 950PR/950DT支持。试验接口。

支持场景：连续数据搬出、随路格式转换（Fractal到ND/NZ等）、Batch多矩阵搬出、随路量化（QuantPre）、随路ReLU（ReluPre）、F32通道切分（F32ChannelSplit）、INT8通道合并（Int8ChannelMerge）。函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [BatchCopy](../cube_store_key_features/batch_copy.md)（`related`）：BatchCopy 是 L0C→GM Copy 在最外层增加 Batch 轴的变体，沿用目标格式与搬出参数并一次处理多块矩阵。
- [Copy](copy_l0_c_to_ub.md)（`related`）：《Copy》明确“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”；它与《Copy》的“将L0C Buffer中的矩阵计算结果搬运到Unified Buffer，支持随路格式转换、量化输出、Relu和batch模式等特性。”在实际调用参数、数据流或结果校验上直接衔接。
- [CopyL1ToFixpipe](../cube_compute_load/copy_l1_to_fixpipe.md)（`related`）：使用 tensor QuantPre 搬出时，量化 tensor 需先从 L1 搬到 Fixpipe；CopyL1ToFixpipe 是 CopyL0CToGM 随路量化的上游参数准备。
- [DataCopyL0CToGM](../../cube_compute/cube_compute_store/data_copy_l0_c_to_gm.md)（`related`）：两接口都把 L0C 结果搬到 GM 并支持格式转换、量化和 ReLU；TensorAPI Copy 自动由 Layout 推导参数，ISASI DataCopy 显式配置 DataCopyCO12DstParams。
- [Int8 Channel Merge](../cube_store_key_features/int8_channel_merge.md)（`related`）：Int8 Channel Merge 只在 L0C→GM Copy 的目的格式为 NZ 且 dtype 为 int8/uint8（950 还含部分 FP8）时自动发生。
- [UnitFlag](../mmad_compute_key_features/unit_flag.md)（`related`）：《UnitFlag》处理“unitFlag的核心功能体现为：Mmad和Copy接口引入了单元标志（unit-flag）机制，通过以内存块为粒度实现精细化的数据同步，从而有效降低同步延迟，提升系统整体性能。当UnitFlag开关打开后，对于L0C Buffer中的每个内存块（512B），提供一个单元标志位，用于指示该块是否可读或可写。”。《Copy》提供“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”，其具体合同或探针直接接入UnitFlag 在 Mmad 产出与 L0C 搬出之间的 512B 细粒度同步和方向配置。
- [基础API随路量化](../cube_store_key_features/quant_pre.md)（`related`）：《Copy》明确“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性。”；它与《基础API随路量化》的“随路量化是矩阵计算结果从L0C Buffer搬出到Global Memory或Unified Buffer过程中的数据转换能力。L0C Buffer到Global Memory/Unified Buffer搬运根据是否传入quant参数自动选择不量化、直接cast、scalar量化或tensor量化模式。”在实际调用参数、数据流或结果校验上直接衔接。
- [Int8 Channel Merge](../../cube_compute/cube_store_key_features/int8_channel_merge.md)（`same_topic`）：焦点处理Int8 Channel Merge 在 L0C 搬出时的格式、量化与通道配置；Copy正文说明“将L0C Buffer中的矩阵计算结果搬运到Global Memory，支持随路格式转换、量化输出、Relu和batch模式等特性”。候选控制该搬出路径的通道合并、量化参数或 L0C→GM 执行位置。
<!-- cannbot:related:end -->
