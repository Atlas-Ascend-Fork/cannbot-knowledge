---
type: API
title: DataCopyPad（GMToL1非对齐数据搬运）
description: 该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopyPad_GMToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# DataCopyPad（GM到L1带Padding搬运）

将Global Memory中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding（补齐）。用于源数据长度不满足对齐要求时自动补齐。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams、padParams（含padding值和方向）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad stride 表示 block 间隙](../../../../../runbooks/precision/datacopypad_stride_is_inter_block_gap.md)（`exemplifies`）：DataCopyPad stride 表示 block 间隙 与《DataCopyPad（GMToL1非对齐数据搬运）》的实质衔接是：这些卡都直接解释 DataCopyPad 的 stride 是有效 block 后的 gap，并覆盖32B单位、窄尾padding、逐行复制、非连续子块、NDDMA stride及官方GM→L1参数契约。
- [DataCopy](data_copy_gm_to_l1_continuous.md)（`related`）：非对齐尾块需 Pad 版本，普通 continuous 不隐式补齐。
- [DataCopy](data_copy_gm_to_l1_nd2_nz.md)（`related`）：《DataCopy》明确“将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopyPad](../../memory_vector_compute/data_move/data_copy_pad_gm_to_ub.md)（`related`）：《DataCopyPad》明确“将数据从GM非对齐搬运至UB，可根据需要自行填充数据。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [DataCopyPad（UBToL1非对齐数据搬运）](data_copy_pad_ub_to_l1.md)（`related`）：《DataCopyPad（UBToL1非对齐数据搬运）》明确“将 Unified Buffer 中的数据经 Matmul workspace 搬运至 L1 Buffer，并支持非对齐数据的 Padding。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《DataCopyPad（GMToL1非对齐数据搬运）》明确提供“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《DataCopyPad（GMToL1非对齐数据搬运）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
