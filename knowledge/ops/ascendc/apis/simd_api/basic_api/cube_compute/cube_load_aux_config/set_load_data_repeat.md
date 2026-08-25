---
type: API
title: SetLoadDataRepeat
description: 设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_load_aux_config/SetLoadDataRepeat.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetLoadDataRepeat

设置 LoadData（卷积数据搬运）接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运。头文件 `basic_api/kernel_operator_mm_intf.h`。

参数：repeatParams 为 LoadDataRepeatParam。字段：repeatStride[0,65535]相邻迭代起始地址距离（repeatMode=0 时单位 16 元素，repeatMode=1 时单位与型号相关）、repeatTime[0,255]迭代次数（0 为 NOP）、repeatMode(0=height 方向/1=width 方向)、dstStride 输出矩阵 K 轴偏移（512B 分形为单位，仅 950 支持，950 调用时必须配置）。

约束：height 方向 repeatStride 单位 16 元素，width 方向单位 32/sizeof(data_type) 元素。支持 950/a2/a3/Atlas 200I/500 A2，不支持 Atlas 推理 AI Core/Vector Core/Atlas 训练系列。
