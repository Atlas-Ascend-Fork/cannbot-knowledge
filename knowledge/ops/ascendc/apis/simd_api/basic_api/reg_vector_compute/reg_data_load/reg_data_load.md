---
type: API
title: Reg数据搬入
description: Reg数据搬入接口索引页，涵盖LoadAlign连续/非连续、LoadUnAlign、MaskReg搬入、Gather离散搬入及Load/Move。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_load/reg_data_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg数据搬入

Reg 数据搬入接口集合，将 UB 侧 LocalTensor 数据加载到寄存器。LoadAlign 支持连续/非连续对齐搬入；LoadUnAlign 支持连续非对齐搬入；Gather/GatherB 支持按索引离散搬入；MaskReg 搬入支持 LoadAlign 与 MaskGenWithRegTensor 两种方式；Load/Move 为通用搬入接口。需根据数据对齐与访问模式选择。

<!-- cannbot:related:start -->
## 相关

- [LoadDist 错用 DIST_NORM_B32 导致编译失败](../../../../../runbooks/compilation/reg_load_and_store_use_distinct_dist_enums.md)（`exemplifies`）：LoadDist 错用 DIST_NORM_B32 导致编译失败 与《Reg数据搬入》的实质衔接是：该编译失败来自把 StoreDist::DIST_NORM_B32 套到 Reg LoadAlign；Reg load/LoadAlign 与 Store 总览直接展示 LoadDist 和 StoreDist 是两套枚举及正常 fp32 布局的配对。
- [AscGather](../../../c_api/vector_compute/asc_gather.md)（`related`）：AscGather 与《Reg数据搬入》的实质衔接是：AscGather 的 offset 是逐元素收集地址；Reg/Memory Gather 与各错位 runbook 直接解释偏移、基址、维序和非轴步长的正确构造。
- [Gather](gather_discrete.md)（`related`）：集合页把按索引离散搬入分流到 Gather，而连续地址使用 Load/LoadAlign/LoadUnAlign。
- [LoadUnAlign](load_un_align_continuous.md)（`related`）：集合页按起点非 32B 对齐选择 LoadUnAlign，并区别于连续对齐 LoadAlign。
<!-- cannbot:related:end -->
