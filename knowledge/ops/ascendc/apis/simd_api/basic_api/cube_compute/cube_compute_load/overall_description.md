---
type: API
title: Cube计算(ISASI)总体说明
description: 矩阵计算的搬入是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现Global Memory到L0A Buffer/L0B Buffer之间的数据高效传输。该类接口提供了多种数据搬运模式，能够满足矩阵计算中左右矩阵等数据的搬运需求，通常与Mmad接口配合使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/overall_description.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# Cube计算(ISASI)总体说明

矩阵计算搬入接口实现 Global Memory、Unified Buffer 到 L1 Buffer、L0A/L0B Buffer 之间的数据传输，通常与 Mmad 配合使用。支持 2D 矩阵搬运、3D 卷积 im2col 展开、ND2NZ/DN2NZ 格式转换、压缩数据解压、矩阵转置、4选2结构化稀疏等场景。

数据通路对齐要求：GM 源地址 1 字节；L1 Buffer 目的 32 字节、源 32 字节；L0A/L0B Buffer 目的 512 字节；BiasTable Buffer 目的 64 字节；Fixpipe Buffer 目的 128 字节。Ascend 950PR/950DT 删除了 GM 到 L0A/L0B 的直连通路，需拆分为 GM→L1→L0A/L0B 两步搬运；该型号下 LoadDataWithTranspose 仅支持 L1→L0B 通路。

GM→L1 接口含 DataCopy（连续/高维切分/ND2NZ/DN2NZ）、DataCopyPad（非对齐补齐）、LoadData（2D/2DV2）。UB→L1 接口类似。L1→L0A/B 接口含 LoadData（2D/卷积/V2/BitMode/MX）、LoadDataWithTranspose、LoadDataWithSparse。辅助接口含 Fill、SetFmatrix、SetLoadDataBoundary、SetLoadDataRepeat、SetLoadDataPaddingValue、LoadDataUnzip、LoadImageToLocal、LoadUnzipIndex、SetAippFunctions。

<!-- cannbot:related:start -->
## 相关

- [Cube计算(ISASI)总体说明](../cube_compute_store/overall_description.md)（`related`）：Cube load 总体说明覆盖 Mmad 前的 GM/UB→L1/L0A/L0B 输入路径，与本卡的 L0C→GM/L1/UB 输出路径拼成完整矩阵数据流。
- [L1与L0数据搬运](../../data_move_guide/l1_l0_data_move.md)（`related`）：L1与L0数据搬运 与《Cube计算(ISASI)总体说明》的实质衔接是：该概述限定 L1→L0A/L0B 的 LoadData 与 L0C→L1 的 DataCopy/Fixpipe 路径，并给出 512B 分形和对齐约束；矩阵搬入约束、普通矩阵流程与 Cube 编程材料解释这些路径在 Mmad 前后的角色。
- [LoadDataWithStride](load_data_with_stride.md)（`related`）：总体说明给出 950 上 GM→L0 直连删除、L0A/B 512B 对齐及可用搬入模式，可用于验证 LoadDataWithStride 所处通路和地址前提。
- [LoadDataWithTranspose](load_data_with_transpose.md)（`related`）：《LoadDataWithTranspose》处理“完成普通矩阵计算所需的2D格式数据搬运，搬运过程中伴随转置操作，支持L1 Buffer到L0A/L0B Buffer通路。”。《Cube计算(ISASI)总体说明》提供“矩阵计算的搬入是Ascend C编程框架中用于数据搬运的一类核心接口，主要实现Global Memory到L0A Buffer/L0B Buffer之间的数据高效传输。该类接口提供了多种数据搬运模式，能够满足矩阵计算中左右矩阵等数据的搬运需求，通常与Mmad接口配合使用。”，其具体合同或探针直接接入带转置 LoadData 的 L1→L0 搬运路径、输入约束和 Buffer 分形。
- [矩阵计算的搬入总体说明](../../cube_compute_tensor_api/cube_compute_load/overall_description.md)（`related`）：矩阵计算的搬入总体说明 与《Cube计算(ISASI)总体说明》的实质衔接是：Cube Load 总体说明用于选择 GM→L1 与 L1→各 L0/Bias/Fixpipe 通路；分形格式、缓存位置和搬入约束决定 Copy 路径。
- [BroadCastVecToMMISASI](broad_cast_vec_to_mm_isasi.md)（`same_topic`）：Load 总页解释 Vec→MM 广播的数据格式、目标 buffer 和限制。
<!-- cannbot:related:end -->
