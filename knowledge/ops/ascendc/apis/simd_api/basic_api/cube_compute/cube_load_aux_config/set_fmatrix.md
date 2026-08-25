---
type: API
title: SetFmatrix
description: 调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetFmatrix.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetFmatrix

调用 LoadData（卷积数据搬运）时设置 FeatureMap 属性描述。当 LoadData 模板参数 isSetFMatrix 为 false 时，须通过本接口设置 FeatureMap 属性。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：l1H[1,32767]源操作数高度、l1W[1,32767]源操作数宽度、padList[4]（left/right/top/bottom，每个 [0,255]，默认 {0,0,0,0}）、fmatrixMode（FmatrixMode 类型，当前仅支持 FMATRIX_LEFT，左右矩阵均用该配置）。

支持 950/a2/a3/Atlas 200I/500 A2/Atlas 推理 AI Core/Kirin X90/9030，不支持 Vector Core 和 Atlas 训练系列。

<!-- cannbot:related:start -->
## 相关

- [Cube矩阵计算编程](../../../../../guides/programming_guide/programming_model/ai_core_simd_programming/c_pointer_programming/cube_matrix_computation.md)（`explains`）：Cube矩阵计算编程 与《SetFmatrix》的实质衔接是：Cube C 指针编程按 GM→L1→L0、Mmad、L0C→GM 四阶段执行；所选架构、分形、Fmatrix、搬运、Mmad 和 tile 边界材料分别约束每一阶段。
- [矩阵向量乘](../../../../../guides/operator_practice/simd_operator_impl/matrix_advanced_api/feature_scenarios/matrix_vector_multiply.md)（`explains`）：矩阵向量乘 与《SetFmatrix》的实质衔接是：矩阵向量乘法通过 Matmul/MxMatmul 配置、fmatrix/LoadData 搬入与 GEMV 原语实现，所选材料对应高层接口和底层数据通路。
- [较小矩阵长驻L1 Buffer，仅分次搬运较大矩阵](../../../../../guides/operator_practice/simd_operator_optimization/matrix_compute/small_matrix_l1_buffer.md)（`explains`）：SetFmatrix 配置 L1 中矩阵的形状/步长，是实现较小矩阵长驻并反复参与 Cube 加载的基础契约。
- [AscL13dFmatrixConfig](../../../c_api/struct/asc_l13d_fmatrix_config.md)（`related`）：SetFmatrix 与《AscL13dFmatrixConfig》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [AscSetL13dFmatrix](../../../c_api/cube_data_move/asc_set_l13d_fmatrix.md)（`related`）：《AscSetL13dFmatrix》的任务是“设置3D搬运接口的Feature map属性描述，用于配置填充数值。”。《SetFmatrix》具体提供“调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。”，它直接用于3D L1→L0 搬运的 Fmatrix、尺寸、padding、repeat 配置。
- [AscSetL13dFmatrixB](../../../c_api/cube_data_move/asc_set_l13d_fmatrix_b.md)（`related`）：SetFmatrix 与《AscSetL13dFmatrixB》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [LoadData](../cube_compute_load/load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《SetFmatrix》具体提供“调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](../cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《SetFmatrix》明确提供“调用LoadData（卷积数据搬运）时设置FeatureMap的属性描述，包括l1H、l1W、padList和fmatrixMode，需在LoadData接口前调用。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadData（BitMode卷积数据搬运）](../cube_compute_load/load_data_3_d_bit_mode.md)（`related`）：SetFmatrix 与《LoadData（BitMode卷积数据搬运）》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [LoadImageToLocal](load_image_to_local.md)（`related`）：LoadImageToLocal 与《SetFmatrix》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [SetFmatrixBitMode](set_fmatrix_bit_mode.md)（`same_topic`）：SetFmatrixBitMode 与《SetFmatrix》的实质衔接是：SetFmatrixBitMode 以位域配置卷积 LoadData 的 feature-map 属性；SetFmatrix、BitMode LoadData、MmadBitMode 与 C Fmatrix 配置是同一搬入协议的设置和消费端。
- [SetLoadDataBoundary](set_load_data_boundary.md)（`same_topic`）：SetFmatrix 与《SetLoadDataBoundary》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [SetLoadDataPaddingValue](set_load_data_padding_value.md)（`same_topic`）：SetFmatrix 与《SetLoadDataPaddingValue》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
- [矩阵搬入辅助配置接口](cube_load_aux_config.md)（`same_topic`）：SetFmatrix 与《矩阵搬入辅助配置接口》的实质衔接是：SetFmatrix 必须在卷积 LoadData 前声明 H/W/padding/fmatrixMode；BitMode、C API config 与 Cube 搬入材料描述同一配置在数据加载阶段的消费。
<!-- cannbot:related:end -->
