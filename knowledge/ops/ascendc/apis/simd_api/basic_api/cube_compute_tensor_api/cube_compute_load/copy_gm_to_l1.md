---
type: API
title: CopyGmToL1
description: 通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_TensorAPI/cube_compute_load/Copy_GMToL1.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Copy（GM到L1 Buffer数据搬运）

通过统一Copy接口将Global Memory数据搬运到L1 Buffer，用于矩阵计算输入搬入。搬运参数由Tensor Layout自动推导，用户无需额外传入搬运参数。仅Ascend 950PR/950DT支持。试验接口，后续可能调整。

支持场景：连续数据搬入（格式不变）、高维切分搬入（多段搬运）、随路格式转换搬入（ND/DN到NZ/ZN等）、Batch多矩阵搬入（支持ND2ND/ND2NZ/DN2NZ等多种格式转换）、Scale数据搬入（MX矩阵计算）、卷积特征图搬入（NC1HWC0格式转换）。

函数原型通过模板参数指定AtomType、DstTensor和SrcTensor类型，搬运块数和长度由Layout推导。约束：遵循Cube计算地址对齐约束。头文件：tensor_api/tensor.h。

<!-- cannbot:related:start -->
## 相关

- [AIV核上的ND2NZ格式转换](../../../../../guides/operator_practice/best_practices/matmul_tuning_cases/aiv_nd2nz_conversion.md)（`explains`）：AIV 把 NZ 结果写入 workspace 后，Matmul 仍需把该 GM 数据搬入 L1；CopyGmToL1 的连续/格式不变路径承担这一后继步骤。
- [CopyL1ToL0A](copy_l1_to_l0_a.md)（`related`）：Cube Tensor 数据链先用 CopyGmToL1 把矩阵从 GM 搬到 L1，再由 focal CopyL1ToL0A 装入 L0A，二者共享 Layout 驱动的分形搬运契约。
- [CopyL1ToL0B](copy_l1_to_l0_b.md)（`related`）：B 数据先 GM→L1，再由本接口进入 L0B。
- [LoadData](../../cube_compute/cube_compute_load/load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《CopyGmToL1》明确提供“通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [MakeTensor](../../data_structure_tensor_api/tensor_structure/make_tensor.md)（`related`）：CopyGmToL1 依赖带 Engine 物理位置和 Layout 的 Tensor 参数来推导 GM→L1 搬运形态；MakeTensor 正是把 HardwareMemPtr 与 Layout 绑定为可传给 Copy 的 Tensor。
- [CopyL1ToFixpipe](copy_l1_to_fixpipe.md)（`same_topic`）：CopyL1ToFixpipe 与《CopyGmToL1》的实质衔接是：CopyL1ToFixpipe 把随路量化参数送入 Fixpipe，必须与 L0C 搬出、量化模式和 SetFixPipe* 地址/裁剪/预量化配置一起使用。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_gm_to_l1_continuous.md)（`same_topic`）：Tensor API 提供同一 GM→L1 连续搬运。
- [DataCopy](../../cube_compute/cube_compute_load/data_copy_gm_to_l1_nd2_nz.md)（`same_topic`）：DataCopy 的核心契约是“将矩阵从Global Memory搬运至L1 Buffer，并在搬运过程中完成ND到NZ格式的转换”；CopyGmToL1 补充“通过Tensor API的Copy接口将Global Memory数据搬运到L1 Buffer，支持随路格式转换和Batch多矩阵搬入”。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《CopyGmToL1》的实质衔接是：Tensor API 分形介绍决定 CopyGmToL1、CopyL1ToL0A/B、Mmad 与 Copy 搬出的 shape/layout；辅助分形和搬出关键特性解释各阶段格式转换。
- [矩阵计算输入搬运约束](../../cube_compute/cube_compute_load/cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《CopyGmToL1》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
