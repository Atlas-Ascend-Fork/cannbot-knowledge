---
type: API
title: 矢量数据搬运
description: 矢量数据搬运类接口汇总，提供GM与UB、UB与L1间的连续搬运、高维切分及padding配置能力。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_data_move/vector_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 矢量数据搬运

矢量数据搬运接口提供GM与UB、UB与L1之间的数据搬运能力。GM与UB间含asc_copy_gm2ub/ub2gm及其_align对齐变体，asc_ndim_copy_gm2ub支持多维切分搬运。UB内与L1间含asc_copy_ub2ub/ub2l1。
循环搬运参数通过asc_set_gm2ub_loop_size/loop1_stride/loop2_stride和asc_set_ub2gm_loop系列配置。多维padding通过asc_set_ndim_loop_stride/ndim_pad_count/ndim_pad_value和asc_set_copy_pad_val配置。asc_set_gm2ub_pad已废弃。

<!-- cannbot:related:start -->
## 相关

- [AscSetGm2ubLoop1Stride](asc_set_gm2ub_loop1_stride.md)（`related`）：AscSetGm2ubLoop1Stride 与《矢量数据搬运》的实质衔接是：Loop1Stride 必须与 Loop2/LoopSize 一起配置后由 GM→UB copy 消费；对齐变体决定这些循环步长作用的实际搬运。
- [GmUbDataMove](../../basic_api/data_move_guide/gm_ub_data_move.md)（`related`）：GmUbDataMove 与《矢量数据搬运》的实质衔接是：GM↔UB 总览按连续、高维、切片、ND2NZ/NZ2ND、NDDMA 和 DataCopyPad 选择通路；所选 NDDMA 卡逐一约束 padding、维度和 stride。
- [AscCopyUb2GmAlign](asc_copy_ub2gm_align/asc_copy_ub2gm_align_arch_2201.md)（`same_topic`）：AscCopyUb2GmAlign 与《矢量数据搬运》的实质衔接是：UB→GM aligned 搬运与普通/2201 变体、反向 GM→UB、pad 和 loop 配置组成同一非对齐数据通路。
- [asc_copy_ub2gm](asc_copy_ub2gm/asc_copy_ub2gm_arch_2201.md)（`same_topic`）：asc_copy_ub2gm 与《矢量数据搬运》的实质衔接是：UB→GM 基础搬运与 aligned 变体、反向 GM→UB 组成数据通路；loop stride/size 与 pad 值必须在调用前按 2201 契约配置。
<!-- cannbot:related:end -->
