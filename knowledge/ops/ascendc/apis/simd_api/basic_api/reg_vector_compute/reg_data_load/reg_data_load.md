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
