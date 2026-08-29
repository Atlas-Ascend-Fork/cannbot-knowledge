---
type: API
title: L1与L0数据搬运
description: L1 Buffer与L0 Buffer之间的数据搬运提供了灵活的接口支持，能够充分适配多样化的计算场景（见表1）。其中，L1 Buffer-\>L0A Buffer、L1 Buffer-\>L0B Buffer的数据搬运用于矩阵计算（参考矩阵计算的搬入），L0C Buffer-\>L1 Buffer用于矩阵计算的搬出，完成矩阵计算的输出流程（参考矩阵计算的搬出）。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/data_move_guide/L1_L0_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# L1与L0数据搬运

L1 Buffer 与 L0 Buffer 间数据搬运接口概述。L1→L0A/L0B 支持 LoadData（2D 矩阵搬运/卷积数据搬运/BitMode/MX）、LoadDataWithTranspose（转置搬运）、LoadDataWithSparse（稀疏搬运）。L0C→L1 支持 DataCopy 和 Fixpipe（随路量化/ReLU）。L1→BiasTable/Fixpipe 支持参数搬运。LoadData 以 512B 分形为单位，L0A/L0B 地址需 512B 对齐。具体接口详见 cube_compute_ISASI 章节。
