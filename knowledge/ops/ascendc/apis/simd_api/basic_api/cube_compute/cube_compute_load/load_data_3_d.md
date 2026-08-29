---
type: API
title: LoadData
description: 将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_3D.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LoadData 3D

将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。支持高维数据的分块搬运，通过LoadData3DParams配置各维度切分参数。3D模式适用于卷积等高维数据场景。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [SetLoadDataBoundary](../cube_load_aux_config/set_load_data_boundary.md)（`related`）：设置 LoadData（卷积数据搬运）接口的 L1 Buffer（A1/B1）边界值。；将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。。SetLoadDataBoundary 配置的正是 LoadData 从 L1 到 L0A/L0B 搬运时的源地址环绕边界，需与实际 3D 搬运调用合用。
- [SetLoadDataPaddingValue](../cube_load_aux_config/set_load_data_padding_value.md)（`related`）：设置 LoadData（卷积数据搬运）接口的 Pad 填充值。当 LoadData 模板参数 isSetPadding 为 false 时须通过本接口设置；为 true 时本接口不生效。；将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。。SetLoadDataPaddingValue 为 LoadData 3D 卷积搬运提供模板未内嵌 padding 时的 Pad 值配置，二者在同一次搬运调用中衔接。
- [LoadData（BitMode卷积数据搬运）](load_data_3_d_bit_mode.md)（`same_topic`）：LoadData 3D的位宽模式变体，支持int4等特定位宽数据类型的高维数据搬运。；将数据从L1 Buffer搬运到L0A或L0B Buffer的3D模式搬运接口。。BitMode 端是同一 L1 到 L0A/L0B 三维搬运的特定位宽变体，基础端给出共同的数据通路与分块语义，互读可按常规数据类型或 int4 等位宽选择接口。
<!-- cannbot:related:end -->
