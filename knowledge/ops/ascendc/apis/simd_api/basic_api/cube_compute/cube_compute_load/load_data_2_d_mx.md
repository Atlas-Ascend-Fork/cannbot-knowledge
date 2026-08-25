---
type: API
title: LoadData
description: 完成矩阵计算所需的左右矩阵数据及对应量化系数矩阵数据的搬运，左右矩阵以512字节分形为单位，量化系数矩阵以32字节分形为单位。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D_MX.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LoadData 2D MX

LoadData 2D的MX（微缩放）模式变体，用于MX矩阵计算中带Scale系数的数据搬运。支持ScaleA/ScaleB数据的随路搬运。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [CopyL1ToL0ScaleB](../../cube_compute_tensor_api/cube_compute_load/copy_l1_to_l0_scale_b.md)（`related`）：The tensor-API Copy route makes the ScaleB half of MX movement explicit, while the focal LoadData carries right-matrix scale data in its combined interface.
- [LoadData](load_data_2_d.md)（`related`）：《LoadData》明确“完成矩阵计算所需的左右矩阵数据及对应量化系数矩阵数据的搬运，左右矩阵以512字节分形为单位，量化系数矩阵以32字节分形为单位。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_2_d_v2.md)（`related`）：《LoadData》明确“完成矩阵计算所需的左右矩阵数据及对应量化系数矩阵数据的搬运，左右矩阵以512字节分形为单位，量化系数矩阵以32字节分形为单位。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadData》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
