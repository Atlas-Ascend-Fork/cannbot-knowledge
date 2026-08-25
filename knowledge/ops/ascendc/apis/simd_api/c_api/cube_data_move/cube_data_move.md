---
type: API
title: 矩阵数据搬运
description: 矩阵数据搬运接口索引页，涵盖asc_copy_gm2l0a/l0b/l1、asc_copy_l0c2gm及asc_fill_l0a/l0b/l1等。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/cube_data_move.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# 矩阵数据搬运

矩阵数据搬运接口覆盖GM、L1、L0A、L0B、L0C、UB之间的数据通路。GM到L1/L0A/L0B方向有asc_copy_gm2l0a/gm2l0b/gm2l1及其align/nd2nz变体；L0C到GM/L1/UB方向有asc_copy_l0c2gm/l0c2l1/l0c2ub。
L1到L0A/L0B/L0C/UB/GM方向有asc_copy_l12l0a/l12l0b/l12l0c/l12ub/l12gm及其trans/mx/sparse变体。asc_fill_l0a/l0b/l1提供填充接口，asc_load_image_to_cbuf加载图像到CBUF。
asc_set_gm2l1_loop_size/loop1_stride/loop2_stride/pad和asc_set_l13d_fmatrix/padding/rpt/size配置搬运循环步长、padding和3D矩阵参数。asc_set_l0c_copy_params/prequant配置L0C搬运与随路反量化。
