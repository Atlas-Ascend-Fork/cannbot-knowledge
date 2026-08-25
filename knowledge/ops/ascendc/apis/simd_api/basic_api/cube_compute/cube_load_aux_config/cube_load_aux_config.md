---
type: API
title: 矩阵搬入辅助配置接口
description: 矩阵搬入辅助配置接口集，包含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataPaddingValue 等。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/cube_load_aux_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵搬入辅助配置接口

矩阵计算 ISASI 搬入阶段的辅助配置接口，用于设置搬运过程中的填充、分形与边界等参数。
包含 SetFmatrix/SetFmatrixBitMode 设置分形矩阵参数，SetLoadDataBoundary/SetLoadDataPaddingValue 设置边界与填充值，SetLoadDataRepeat/SetLoadDataRepeatWithStride 设置重复搬运参数。
另提供 Fill 填充、LoadDataUnzip/LoadUnzipIndex 解压搬运、LoadImageToLocal 图像加载及 SetAippFunctions AIPP 功能配置等接口。

<!-- cannbot:related:start -->
## 相关

- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《矩阵搬入辅助配置接口》说明矩阵搬入辅助配置接口集，包含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataPaddingValue 等。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadImageToLocal](load_image_to_local.md)（`same_topic`）：LoadImageToLocal 与《矩阵搬入辅助配置接口》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetFmatrix](set_fmatrix.md)（`same_topic`）：SetFmatrix 与《矩阵搬入辅助配置接口》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [SetFmatrixBitMode](set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《矩阵搬入辅助配置接口》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [SetLoadDataPaddingValue](set_load_data_padding_value.md)（`same_topic`）：SetLoadDataPaddingValue 与《矩阵搬入辅助配置接口》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [矩阵计算的搬入](../cube_compute_load/cube_compute_load.md)（`same_topic`）：矩阵搬入辅助配置接口 与《矩阵计算的搬入》的实质衔接是：矩阵搬入指南解释本配置集合怎样作用于 LoadData/LoadImage 的 padding、边界和 fmatrix 阶段。
<!-- cannbot:related:end -->
