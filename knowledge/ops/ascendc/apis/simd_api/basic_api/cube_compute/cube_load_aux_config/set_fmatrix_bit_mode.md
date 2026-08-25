---
type: API
title: SetFmatrixBitMode
description: 调用LoadData（卷积数据搬运）时以位域方式设置FeatureMap的属性描述，包括l1H、l1W和padList，需在LoadData接口前调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetFmatrixBitMode.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# SetFmatrixBitMode

SetFmatrix 的 BitMode 变体，以位域方式设置 LoadData（卷积数据搬运）的 FeatureMap 属性描述。当 LoadData 模板参数 isSetFMatrix 为 false 时使用。用于追求极致 Scalar 性能的场景。

参数：param 为 SetFMatrixBitModeParams 结构体（含 l1H、l1W、padList 等位域配置）；fmatrixMode 为 FmatrixMode 类型，当前仅支持 FMATRIX_LEFT。仅 Ascend 950PR/950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《SetFmatrixBitMode》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [矩阵向量乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md)（`explains`）：矩阵向量乘 与《SetFmatrixBitMode》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [LoadData](../cube_compute_load/load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetFmatrixBitMode》具体提供“调用LoadData（卷积数据搬运）时以位域方式设置FeatureMap的属性描述，包括l1H、l1W和padList，需在LoadData接口前调用。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](../cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《SetFmatrixBitMode》明确提供“调用LoadData（卷积数据搬运）时以位域方式设置FeatureMap的属性描述，包括l1H、l1W和padList，需在LoadData接口前调用。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadImageToLocal](load_image_to_local.md)（`related`）：LoadImageToLocal 与《SetFmatrixBitMode》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [AscL13dFmatrixConfig](../../../c_api/struct/asc_l13d_fmatrix_config.md)（`same_topic`）：SetFmatrixBitMode 与《AscL13dFmatrixConfig》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [AscSetL13dFmatrix](../../../c_api/cube_data_move/asc_set_l13d_fmatrix.md)（`same_topic`）：SetFmatrixBitMode 与《AscSetL13dFmatrix》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [AscSetL13dFmatrixB](../../../c_api/cube_data_move/asc_set_l13d_fmatrix_b.md)（`same_topic`）：SetFmatrixBitMode 与《AscSetL13dFmatrixB》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [LoadData（BitMode 2D矩阵搬运）](../cube_compute_load/load_data_2_d_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《LoadData（BitMode 2D矩阵搬运）》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [LoadData（BitMode卷积数据搬运）](../cube_compute_load/load_data_3_d_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [MmadBitMode](../mmad_compute/mmad_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《MmadBitMode》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [SetFmatrix](set_fmatrix.md)（`same_topic`）：SetFmatrixBitMode 与《SetFmatrix》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [矩阵搬入辅助配置接口](cube_load_aux_config.md)（`same_topic`）：SetFmatrixBitMode 与《矩阵搬入辅助配置接口》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
<!-- cannbot:related:end -->
