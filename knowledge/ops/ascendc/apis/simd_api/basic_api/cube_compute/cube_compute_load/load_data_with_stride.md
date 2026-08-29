---
type: API
title: LoadDataWithStride
description: 将NC1HWC0格式的Feature Map完成Image to Column展开后搬入对应内存，支持配置输出矩阵K轴方向偏移量dstStride。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/cube_compute_ISASI/cube_compute_load/LoadDataWithStride.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# LoadDataWithStride

将数据从L1 Buffer搬运到L0A或L0B Buffer，支持源侧带步长的数据搬运。用于源数据在L1中非连续存储时的分块提取搬运。

函数原型通过模板参数指定数据类型。参数包含dstTensor、srcTensor、loadDataParams（含源侧stride和各维度切分信息）。约束：遵循Cube计算地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [SetLoadDataRepeatWithStride](../cube_load_aux_config/set_load_data_repeat_with_stride.md)（`related`）：将数据从L1 Buffer搬运到L0A或L0B Buffer，支持源侧带步长的数据搬运。；设置 LoadDataWithStride 接口的 repeat 参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵 K 轴方向偏移。。前者执行源侧带 stride 的 L1 到 L0A/L0B 搬运，后者直接配置该接口的 repeat 次数与 K 轴偏移，组成多迭代 stride 搬运的参数设置和执行链。
<!-- cannbot:related:end -->
