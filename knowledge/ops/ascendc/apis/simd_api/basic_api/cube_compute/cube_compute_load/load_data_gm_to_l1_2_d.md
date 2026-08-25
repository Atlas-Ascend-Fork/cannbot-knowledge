---
type: API
title: LoadData
description: 完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_GMToL1_2D.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LoadData GM到L1 2D

将数据从Global Memory直接搬运到L1 Buffer的2D模式接口。支持GM到L1的连续数据搬运和格式转换。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [LoadData](load_data_2_d.md)（`related`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_2_d_v2.md)（`related`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_gm_to_l1_2_dv2.md)（`same_topic`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《LoadData》明确提供“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
<!-- cannbot:related:end -->
