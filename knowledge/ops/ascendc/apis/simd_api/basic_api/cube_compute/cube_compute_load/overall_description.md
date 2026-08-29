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

- [LoadDataWithTranspose](load_data_with_transpose.md)（`related`）：“将数据从L1 Buffer搬运到L0A或L0B Buffer，支持在搬运过程中执行转置操作。用于需要在数据搬入时改变矩阵行列排布的场景。”描述通用目的端，而“Ascend 950PR/950DT 删除了 GM 到 L0A/L0B 的直连通路，需拆分为 GM→L1→L0A/L0B 两步搬运；该型号下 LoadDataWithTranspose 仅支持 L1→L0B 通路。”补上 950 的关键收窄；联合阅读可避免在 950 选择 L0A 目的端。
<!-- cannbot:related:end -->
