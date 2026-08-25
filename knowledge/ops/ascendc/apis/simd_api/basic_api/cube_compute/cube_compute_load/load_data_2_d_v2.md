---
type: API
title: LoadData
description: 完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D_V2.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LoadData 2D V2

LoadData 2D的V2版本，提供增强的搬运能力和更灵活的参数配置。支持更复杂的数据排布和格式转换场景。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [LoadData](load_data_2_d_mx.md)（`related`）：《LoadData》明确“完成矩阵计算所需的左右矩阵数据及对应量化系数矩阵数据的搬运，左右矩阵以512字节分形为单位，量化系数矩阵以32字节分形为单位。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_gm_to_l1_2_d.md)（`related`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_2_d.md)（`same_topic`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`same_topic`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《LoadData》提供“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [LoadData（BitMode 2D矩阵搬运）](load_data_2_d_bit_mode.md)（`same_topic`）：LoadData BitMode 与 LoadData 2D V2 都把 L1 数据装载到 L0，并表达相同二维块搬运；差别是参数由 bitfield 还是显式结构表示。
<!-- cannbot:related:end -->
