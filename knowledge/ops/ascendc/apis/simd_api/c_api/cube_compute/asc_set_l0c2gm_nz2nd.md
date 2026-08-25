---
type: API
title: AscSetL0c2gmNz2nd
description: 数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。
tags: [task.lookup, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_compute/asc_set_l0c2gm_nz2nd.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscSetL0c2gmNz2nd

数据搬运过程中进行随路格式转换（NZ格式转换为ND格式）时，通过调用该接口设置格式转换的相关配置。

参数：nd_num(输入): ND矩阵的个数，取值范围为[1, 65535]。；src_nd_stride(输入): 以分形大小为单位的源步长，源相邻NZ矩阵的偏移。取值范围为[0, 65535]，单位为32B。；dst_nd_stride(输入): 目的相邻ND矩阵的偏移。取值范围为[1,  - 1]，单位为元素。

仅 Ascend 950PR/Ascend 950DT 支持。
