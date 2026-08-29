---
type: API
title: reg数据搬入
description: 寄存器侧数据搬入类接口汇总，提供gather、load、loadalign等从UB到矢量数据寄存器的搬运能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/reg_load/reg_load.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# reg数据搬入

寄存器侧数据搬入接口将数据从Unified Buffer加载到矢量数据寄存器。基础接口含asc_load和asc_copy，asc_loadunalign及其pre/postupdate变体处理非对齐加载。
asc_loadalign及其变体支持对齐加载及多种数据变换：brc（广播）、deintlv（解交织）、downsample/upsample（下/上采样）、unpack（解包）等，postupdate变体支持地址寄存器后更新。asc_gather/gather_datablock提供收集式加载。asc_loadalign v1-v6已废弃。
