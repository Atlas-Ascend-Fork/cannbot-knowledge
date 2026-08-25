---
type: API
title: 矩阵计算的搬入
description: 矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/cube_compute_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 矩阵计算的搬入

矩阵计算 ISASI 搬入接口集，提供 GM/L1/L0A/L0B 之间矩阵数据搬运的底层接口。
LoadData 系列支持 2D 矩阵搬运（含 V2、MX、BitMode 变体）、卷积数据搬运、带转置/稀疏/Stride 的搬运；DataCopy 系列支持 GM/L1 与 UB 间连续、高维切分及非对齐搬运，并支持 DN2NZ/ND2NZ 随路格式转换。
另提供 BroadCastVecToMM 向量到矩阵广播、DataCopy(L1ToBiasTable/Fixpipe) 等专用搬运接口，以及 L1-L0A/L0B 内存结构与输入搬运约束说明。
使用前需了解各接口的路径约束与内存对齐要求。

<!-- cannbot:related:start -->
## 相关

- [Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界](../../../../../runbooks/compilation/cube_retcode_0x26_aiv_cube_api.md)（`exemplifies`）：《Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界》说明Cube 核直调 kernel 入口 extern "C" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。；《矩阵计算的搬入》说明矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。。二者在报错的判别核心是未标核类型导致AIV执行LoadData/Mmad等Cube专属指令，需从kernel type和Cube调用两端验证上存在可执行的直接衔接。
- [LoadData](load_data_3_d.md)（`related`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《矩阵计算的搬入》具体提供“矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [LoadData](load_data_gm_to_l1_2_dv2.md)（`related`）：《LoadData》处理“完成普通矩阵计算所需的2D格式数据搬运，以512字节的数据分形为单位从Global Memory搬运至L1 Buffer。”。《矩阵计算的搬入》明确提供“矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。”，其参数、调用或验证步骤直接接入GM 到 L1 二维 LoadData 的 Fmatrix、repeat、边界和地址合同。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《矩阵计算的搬入》提供“矩阵计算 ISASI 搬入接口集，涵盖 LoadData、DataCopy 等 GM/L1/L0A/L0B 间搬运接口及输入搬运约束。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [普通矩阵计算流程（概述）](../overview/cube_compute_flow.md)（`same_topic`）：普通矩阵计算流程（概述） 与《矩阵计算的搬入》的实质衔接是：普通 Cube 流程按 GM→L1→L0A/L0B 搬入、Mmad、L0C 搬出组织；分形、输入约束与数据通路卡解释每一阶段的布局和边界。
- [矩阵搬入辅助配置接口](../cube_load_aux_config/cube_load_aux_config.md)（`same_topic`）：矩阵搬入辅助配置接口 与《矩阵计算的搬入》的实质衔接是：矩阵搬入指南解释本配置集合怎样作用于 LoadData/LoadImage 的 padding、边界和 fmatrix 阶段。
- [矩阵计算分形介绍](../cube_compute_fractal_intro/cube_compute_fractal_intro.md)（`same_topic`）：矩阵计算分形介绍 与《矩阵计算的搬入》的实质衔接是：分形介绍定义 Cube 输入、权重和输出在 L1/L0A/L0B/L0C 的分块布局；详细分形、搬入约束和普通计算流程直接使用这些布局。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《矩阵计算的搬入》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
