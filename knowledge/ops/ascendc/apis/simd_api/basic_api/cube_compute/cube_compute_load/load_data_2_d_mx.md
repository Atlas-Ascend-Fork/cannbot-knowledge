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
