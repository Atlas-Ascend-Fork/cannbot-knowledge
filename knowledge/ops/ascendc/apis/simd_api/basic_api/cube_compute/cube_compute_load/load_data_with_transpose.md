---
type: API
title: LoadDataWithTranspose
description: 完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadDataWithTranspose.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---


# LoadDataWithTranspose

将数据从L1 Buffer搬运到L0A或L0B Buffer，支持在搬运过程中执行转置操作。用于需要在数据搬入时改变矩阵行列排布的场景。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、loadDataParams（含转置配置和各维度切分信息）。约束：遵循Cube计算地址对齐和转置约束。

<!-- cannbot:related:start -->
## 相关

- [AscTranspose](../../../c_api/vector_compute/asc_transpose.md)（`related`）：AscTranspose 与《LoadDataWithTranspose》的衔接是：AscTranspose 与基础/高阶 Transpose 共享转置数据布局；LoadDataWithTranspose 可作为上游搬运转置，tiling 与 noTrans 布局案例说明方向参数必须一致。
- [Cube计算(ISASI)总体说明](overall_description.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《Cube计算(ISASI)总体说明》提供“矩阵计算的搬入是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现Global Memory到L0A Buffer/L0B Buffer之间的数据高效传输。该类接口提供了多种数据搬运模式，能够满足矩阵计算中左右矩阵等数据的搬运需求，通常与Mmad接口配合使用。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍](l1_l0_a_b_memory_structure_intro.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《L1 Buffer、L0A Buffer/L0B Buffer内存结构介绍》提供“为提升数据访问效率和吞吐量，Buffer采用了等容量的内存模块（Bank）结构设计。内存空间被划分为多个Bank，并以Bank为单位进一步分组形成多个Bank Group（BG）；每个Bank Group包含若干Bank，每个Bank都是一个可独立操作的存储单元子模块。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [L1与L0数据搬运](../../data_move_guide/l1_l0_data_move.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《L1与L0数据搬运》提供“L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [SetLoadDataRepeat](../cube_load_aux_config/set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadDataWithTranspose》说明完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [矩阵计算的搬入](cube_compute_load.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《矩阵计算的搬入》提供“矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《矩阵计算输入搬运约束》提供“具体可见表数据通路和存储层级。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [LoadData](load_data_2_d.md)（`same_topic`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《LoadData》提供“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持GM到L0A/L0B Buffer及L1 Buffer到L0A/L0B Buffer通路。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [LoadData](load_data_2_d_v2.md)（`same_topic`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《LoadData》提供“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位，支持L1 Buffer到L0A/L0B Buffer通路。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [LoadData（BitMode 2D矩阵搬运）](load_data_2_d_bit_mode.md)（`same_topic`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《LoadData（BitMode 2D矩阵搬运）》提供“负责完成普通矩阵计算所需的2D格式数据的搬运，以大小为512字节的数据分形为单位进行搬运，支持的数据通路为：L1 Buffer->L0A Buffer、L1 Buffer->L0B Buffer。 本接口与LoadData（2D矩阵搬运V2）接口的差异在于参数的传入方式不同，本接口传入的是一个联合体结构Load2DBitModeParam。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [Transpose](../../../adv_api/tensor_transform/transpose.md)（`same_topic`）：《Transpose》处理“对输入数据进行数据排布及Reshape操作，支持NZ与ND格式间的多种轴互换和转置场景。”。《LoadDataWithTranspose》明确提供“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”，其参数、调用或验证步骤直接接入Transpose 的 Tiling、转置搬运、布局转换和轴顺序验证。
<!-- cannbot:related:end -->
