---
type: API
title: SetLoadDataRepeatWithStride
description: 设置LoadDataWithStride接口的repeat参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵K轴方向偏移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataRepeatWithStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# SetLoadDataRepeatWithStride

设置 LoadDataWithStride 接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵 K 轴方向偏移。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：repeatParams 为 LoadDataRepeatParamWithStride 结构体，含迭代次数、步长和 K 轴偏移等配置。仅 Ascend 950PR/950DT 支持。
