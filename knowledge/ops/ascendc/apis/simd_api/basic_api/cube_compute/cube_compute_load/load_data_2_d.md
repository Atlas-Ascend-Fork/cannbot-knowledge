---
type: API
title: LoadData
description: 完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadData_2D.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---


# LoadData 2D

将数据从L1 Buffer搬运到L0A或L0B Buffer的2D模式搬运接口。支持连续数据搬运和基本的格式转换。通过LoadData2DParams配置搬运参数。函数原型通过模板参数指定数据类型和搬运方向（L0A或L0B）。参数包含dstTensor（L0A/L0B目的）、srcTensor（L1源）、loadDataParams（搬运参数含各维度切分、步长、偏移等）。约束：遵循Cube计算地址对齐和数据排布约束。

<!-- cannbot:related:start -->
## 相关

- [SIMD算子实现耦合模式](../../../../../guides/operator_practice/simd_operator_impl/matrix_basic_api/coupled_mode.md)（`explains`）：《SIMD算子实现耦合模式》说明>本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。；《LoadData》说明完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。。二者在耦合Cube范式的CopyIn/Split/Compute/CopyOut直接由DataCopy、LoadData、Mmad和TQue交接实现上存在可执行的直接衔接。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_leakyrelu_fusion_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《LoadData》的实质衔接是：Matmul+LeakyRelu 中级优化的正文直接串联 LoadData/Mmad/LeakyRelu、Load/Store、PipeBarrier、SetFlag 和 UnitFlag；所选故障卡约束这条融合流水。
- [中级性能优化](../../../../../guides/operator_practice/typical_operator_cases/simd_operator_impl/matmul_matrix_operator/intermediate_optimization.md)（`explains`）：中级性能优化 与《LoadData》的实质衔接是：Matmul 中级优化直接使用 GM/L1/L0 搬入、LoadData、Mmad 和 UnitFlag，前后阶段及 UnitFlag 指南支撑同一流水。
- [LoadData](load_data_2_d_mx.md)（`related`）：《LoadData》明确“完成矩阵计算所需的左右矩阵数据及对应量化系数矩阵数据的搬运，左右矩阵以512字节分形为单位，量化系数矩阵以32字节分形为单位。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData](load_data_gm_to_l1_2_d.md)（`related`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadData（BitMode 2D矩阵搬运）](load_data_2_d_bit_mode.md)（`related`）：《LoadData（BitMode 2D矩阵搬运）》明确“负责完成普通矩阵计算所需的2D格式数据的搬运，以大小为512字节的数据分形为单位进行搬运，支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（2D矩阵搬运V2）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load2DBitModeParam。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [SetLoadDataRepeat](../cube_load_aux_config/set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadData》说明完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadData](load_data_2_d_v2.md)（`same_topic`）：《LoadData》明确“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”；它与《LoadData》的“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”在实际调用参数、数据流或结果校验上直接衔接。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`same_topic`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《LoadData》提供“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [SetLoadDataPaddingValue](../cube_load_aux_config/set_load_data_padding_value.md)（`same_topic`）：SetLoadDataPaddingValue 与《LoadData》的实质衔接是：该配置在卷积 LoadData 前设定 padValue，Fmatrix/配置总览与 C API setter 是配置端；padding 参与数故障说明填充值不得进入有效 reduce count。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《LoadData》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
<!-- cannbot:related:end -->
