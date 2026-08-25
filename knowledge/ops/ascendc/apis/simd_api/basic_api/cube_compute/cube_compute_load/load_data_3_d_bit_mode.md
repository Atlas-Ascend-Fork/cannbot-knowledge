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

- [SetFmatrix](../cube_load_aux_config/set_fmatrix.md)（`related`）：SetFmatrix 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [SetLoadDataPaddingValue](../cube_load_aux_config/set_load_data_padding_value.md)（`related`）：SetLoadDataPaddingValue 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [LoadData](load_data_3_d.md)（`same_topic`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《LoadData（BitMode卷积数据搬运）》具体提供“LoadData（BitMode卷积数据搬运）用于完成image to column操作，将多维feature map转为二维矩阵。支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（卷积数据搬运）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load3DBitModeParam。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [MmadBitMode](../mmad_compute/mmad_bit_mode.md)（`same_topic`）：LoadData（BitMode卷积数据搬运）说明LoadData（BitMode卷积数据搬运）用于完成image to column操作，将多维feature map转为二维矩阵。支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（卷积数据搬运）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load3DBitModeParam。
- [SetFmatrixBitMode](../cube_load_aux_config/set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
<!-- cannbot:related:end -->
