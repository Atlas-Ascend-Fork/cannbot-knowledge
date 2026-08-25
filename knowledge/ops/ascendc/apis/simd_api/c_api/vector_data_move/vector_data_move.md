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
