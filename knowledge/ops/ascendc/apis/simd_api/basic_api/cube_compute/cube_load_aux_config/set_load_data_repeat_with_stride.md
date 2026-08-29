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

<!-- cannbot:related:start -->
## 相关

- [LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)（`related`）：将数据从L1 Buffer搬运到L0A或L0B Buffer，支持源侧带步长的数据搬运。；设置 LoadDataWithStride 接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵 K 轴方向偏移。。前者执行源侧带 stride 的 L1 到 L0A/L0B 搬运，后者直接配置该接口的 repeat 次数与 K 轴偏移，组成多迭代 stride 搬运的参数设置和执行链。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`related`）：焦点卡写明“repeatStride［0,65535］相邻迭代起始地址距离”，候选卡写明“设置 LoadDataWithStride 接口的 repeat 参数”。前者服务普通 LoadData，后者服务 LoadDataWithStride，可据搬运接口选择 repeat 配置。
<!-- cannbot:related:end -->
