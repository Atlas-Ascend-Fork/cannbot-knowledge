---
type: API
title: Reg数据搬出
description: Reg数据搬出接口索引页，涵盖StoreAlign连续/非连续、StoreUnAlign、MaskReg搬出、Scatter离散搬出及Store。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/reg_data_store/reg_data_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Reg数据搬出

Reg 数据搬出接口集合，将寄存器侧数据写回 UB 侧 LocalTensor。StoreAlign 支持连续/非连续对齐搬出；StoreUnAlign 支持连续非对齐搬出；Scatter 支持按索引离散搬出；MaskReg 搬出支持对齐与非对齐两种方式；Store 为通用搬出接口。与 Reg 数据搬入接口对应使用。
