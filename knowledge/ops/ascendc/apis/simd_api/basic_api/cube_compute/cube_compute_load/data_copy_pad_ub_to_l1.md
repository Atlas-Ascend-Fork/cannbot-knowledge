---
type: API
title: DataCopyPad（UBToL1非对齐数据搬运）
description: 将 Unified Buffer 中的数据经 Matmul workspace 搬运至 L1 Buffer，并支持非对齐数据的 Padding。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/DataCopyPad_UBToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# DataCopyPad（UB到L1带Padding搬运）

将Unified Buffer中的数据搬运到L1 Buffer，支持在搬运过程中对数据进行Padding。用于源数据长度不满足对齐要求时自动补齐。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、dataCopyParams、padParams。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [DataCopyPad（GMToL1非对齐数据搬运）](data_copy_pad_gm_to_l1.md)（`related`）：《DataCopyPad（UBToL1非对齐数据搬运）》明确“将 Unified Buffer 中的数据经 Matmul workspace 搬运至 L1 Buffer，并支持非对齐数据的 Padding。”；它与《DataCopyPad（GMToL1非对齐数据搬运）》的“该接口提供从Global Memory到L1 Buffer的数据非对齐搬运功能，可以根据开发者的需要自行填充数据。”在实际调用参数、数据流或结果校验上直接衔接。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《DataCopyPad（UBToL1非对齐数据搬运）》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
