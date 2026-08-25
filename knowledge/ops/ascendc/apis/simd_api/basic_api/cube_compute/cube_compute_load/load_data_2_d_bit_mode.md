---
type: API
title: LoadData（BitMode 2D矩阵搬运）
description: 负责完成普通矩阵计算所需的2D格式数据的搬运，以大小为512字节的数据分形为单位进行搬运，支持的数据通路为：L1 Buffer->L0A
  Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（2D矩阵搬运V2）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load2DBitModeParam。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D_BitMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LoadData 2D BitMode

LoadData 2D的位宽模式变体，支持int4等特定位宽数据类型的搬运。通过额外的BitMode参数配置位宽处理方式。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。
