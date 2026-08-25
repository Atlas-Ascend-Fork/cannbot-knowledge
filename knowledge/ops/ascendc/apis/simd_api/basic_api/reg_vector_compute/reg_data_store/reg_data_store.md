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

<!-- cannbot:related:start -->
## 相关

- [fp32 UB 非 VL 拷贝须用带掩码 Reg](../../../../../runbooks/precision/non_vl_fp32_ub_copy_needs_masked_reg_load_store.md)（`exemplifies`）：fp32 UB 非 VL 拷贝须用带掩码 Reg 与《Reg数据搬出》的实质衔接是：非 VL fp32 UB copy 的修复正文直接调用 UpdateMask、Reg Load/Store；所选 API 与 const/mask 故障卡约束同一尾块实现。
- [StoreAlignNoncontinuous](store_align_noncontinuous.md)（`same_topic`）：StoreAlignNoncontinuous 与《Reg数据搬出》的实质衔接是：StoreAlignNoncontinuous 按 DataBlock stride 将 RegTensor 写回 UB；连续/非对齐变体、LoadAlign 反向分布和非连续搬运指南共同决定布局、地址推进与搬运选择。
- [reg数据搬出](../../../c_api/reg/reg_store/reg_store.md)（`same_topic`）：焦点处理Reg 数据搬出中对齐、非对齐与带 mask store 的选择；Reg数据搬出正文说明“Reg数据搬出接口索引页，涵盖StoreAlign连续/非连续、StoreUnAlign、MaskReg搬出、Scatter离散搬出及Store”。候选把总览中的 store 选择落到 Basic Reg 对应接口或真实非 VL/交错 mask 故障。
<!-- cannbot:related:end -->
