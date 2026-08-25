---
type: API
title: AscL13dFmatrixConfig
description: 用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_l13d_fmatrix_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscL13dFmatrixConfig

asc_l13d_fmatrix_config用于设置asc_copy_l12l0a/asc_copy_l12l0b的3D格式搬运接口的Feature map属性参数。
约束：asc_l13d_fmatrix_config类型的联合体变量被定义后必须对l1_height和l1_width进行赋值以符合实际场景及取值范围要求。
详见源文档获取完整说明。

<!-- cannbot:related:start -->
## 相关

- [矩阵向量乘](../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md)（`explains`）：矩阵向量乘 与《AscL13dFmatrixConfig》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [AscCopyL12L0a](../cube_data_move/asc_copy_l12l0a/asc_copy_l12l0a.md)（`related`）：AscL13dFmatrixConfig 的 height、width 和四周 padding 参数由 AscCopyL12L0a 的 3D feature-map 搬运直接消费。
- [AscCopyL12L0b](../cube_data_move/asc_copy_l12l0b/asc_copy_l12l0b.md)（`related`）：同一 Fmatrix 配置也是 AscCopyL12L0b 3D 权重/特征搬运的几何输入，决定宽高与 padding 解释。
- [AscSetL13dFmatrix](../cube_data_move/asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《AscL13dFmatrixConfig》具体提供“用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [LoadData](../../basic_api/cube_compute/cube_compute_load/load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《AscL13dFmatrixConfig》具体提供“用于设置3D格式搬运接口的Feature map属性参数，包括宽高和四周填充大小。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetFmatrix](../../basic_api/cube_compute/cube_load_aux_config/set_fmatrix.md)（`related`）：SetFmatrix 与《AscL13dFmatrixConfig》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [SetFmatrixBitMode](../../basic_api/cube_compute/cube_load_aux_config/set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《AscL13dFmatrixConfig》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
<!-- cannbot:related:end -->
