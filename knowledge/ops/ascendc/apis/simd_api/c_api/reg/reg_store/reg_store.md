---
type: API
title: reg数据搬出
description: 寄存器侧数据搬出类接口汇总，提供scatter、store、storealign等从矢量数据寄存器到UB的搬运能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_store/reg_store.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# reg数据搬出

寄存器侧数据搬出接口将数据从矢量数据寄存器存储到Unified Buffer。基础接口含asc_store和asc_storeunalign及其post/postupdate变体处理非对齐存储。
asc_storealign及其变体支持对齐存储及多种数据变换：1st（首次）、intlv（交织）、pack（打包）、pack_quarter（四分之一打包）等，postupdate变体支持地址寄存器后更新。asc_scatter提供分散式存储，asc_squeeze_and_storeunalign结合解压与非对齐存储。asc_storealign v1-v5及部分scatter/storeunalign接口已废弃。
