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

- [LoadImageToLocal](load_image_to_local.md)（`related`）：LoadImageToLocal 与《SetLoadDataRepeatWithStride》的实质衔接是：LoadImageToLocal 的 AIPP 配置由边界填充、重复、尺寸和 fmatrix 参数共同决定，C/C++ 入口消费同一搬入契约。
- [LoadDataWithStride](../cube_compute_load/load_data_with_stride.md)（`same_topic`）：SetLoadDataRepeatWithStride 配置的迭代次数、步长和 K 偏移由 LoadDataWithStride 直接消费，构成配置到搬运执行的链路。
- [SetLoadDataRepeat](set_load_data_repeat.md)（`same_topic`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《SetLoadDataRepeatWithStride》说明设置LoadDataWithStride接口的repeat参数，通过一次调用完成多个迭代的数据搬运，并配置输出矩阵K轴方向偏移。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
<!-- cannbot:related:end -->
