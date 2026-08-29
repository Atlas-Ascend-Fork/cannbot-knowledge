---
type: API
title: LoadData（BitMode卷积数据搬运）
description: LoadData（BitMode卷积数据搬运）用于完成image to column操作，将多维feature map转为二维矩阵。支持的数据通路为：L1
  Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（卷积数据搬运）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load3DBitModeParam。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D_BitMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---


# LoadData 3D BitMode

LoadData 3D的位宽模式变体，支持int4等特定位宽数据类型的高维数据搬运。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [LoadData](load_data_3_d.md)（`same_topic`）：LoadData 3D的位宽模式变体，支持int4等特定位宽数据类型的高维数据搬运。；将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。。BitMode 端是同一 L1 到 L0A/L0B 三维搬运的特定位宽变体，基础端给出共同的数据通路与分块语义，互读可按常规数据类型或 int4 等位宽选择接口。
<!-- cannbot:related:end -->
