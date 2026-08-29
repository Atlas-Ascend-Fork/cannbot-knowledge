---
type: API
title: 普通矩阵计算流程（概述）
description: Ascend C针对矩阵计算编程模型提供了四类接口，分别承载Cube核中各个通路的搬运能力和计算能力，如下图所示：
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/overview/cube_compute_flow.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# 普通矩阵计算流程（概述）

Ascend C 矩阵计算编程模型包含三类流程。普通矩阵计算：DataCopy（GM→L1）搬运 A/B 矩阵和 Bias/量化参数 → LoadData（L1→L0A/L0B）加载计算数据 → Mmad（L0A/L0B→L0C）执行矩阵乘加 → Fixpipe（L0C→GM）搬出并执行随路量化/ReLU。

Mx 矩阵计算（仅 950）：额外搬运 scaleA/scaleB 系数矩阵，通过 LoadData（MX）加载到 L0A_MX/L0B_MX Buffer，MmadMx 执行带量化系数的矩阵乘，Fixpipe 搬出。

4 选 2 稀疏矩阵计算（仅 a2/a3）：离线生成稠密矩阵 B 和索引矩阵，LoadDataWithSparse 加载 B 和索引到 L0B/IDX Buffer，MmadWithSparse 根据 4 选 2 索引对 A 稀疏化后执行矩阵乘加，Fixpipe 搬出。
