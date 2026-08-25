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

- [Cube计算(ISASI)总体说明](overall_description.md)（`related`）：总体说明给出 950 上 GM→L0 直连删除、L0A/B 512B 对齐及可用搬入模式，可用于验证 LoadDataWithStride 所处通路和地址前提。
- [SetLoadDataRepeat](../cube_load_aux_config/set_load_data_repeat.md)（`related`）：《SetLoadDataRepeat》说明设置LoadData（卷积数据搬运）接口的repeat参数，通过一次调用完成多个迭代的数据搬运，支持配置迭代次数、步长、方向和K轴偏移。；《LoadDataWithStride》说明将NC1HWC0格式的Feature Map完成Image to Column展开后搬入对应内存，支持配置输出矩阵K轴方向偏移量dstStride。。二者在SetLoadDataRepeat配置的repeat、步长和方向直接控制后续LoadData搬入循环上存在可执行的直接衔接。
- [LoadData](load_data_3_d.md)（`same_topic`）：《LoadData》的任务是“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入L0A/L0B Buffer，也可用于2D格式数据搬运。”。《LoadDataWithStride》具体提供“将NC1HWC0格式的Feature Map完成Image to Column展开后搬入对应内存，支持配置输出矩阵K轴方向偏移量dstStride。”，它直接用于3D LoadData 的 Fmatrix、repeat、boundary、padding 与 L1/L0 地址合同。
- [SetLoadDataRepeatWithStride](../cube_load_aux_config/set_load_data_repeat_with_stride.md)（`same_topic`）：SetLoadDataRepeatWithStride 配置的迭代次数、步长和 K 偏移由 LoadDataWithStride 直接消费，构成配置到搬运执行的链路。
- [矩阵计算输入搬运约束](cube_compute_input_move_constraint.md)（`same_topic`）：矩阵计算输入搬运约束 与《LoadDataWithStride》的实质衔接是：输入搬运约束把 GM/L1/L0A/L0B 的格式、K 对齐和地址对齐落实到 LoadData、CopyGmToL1、CopyL1ToL0A/B 及 sparse/stride/transpose 变体。
<!-- cannbot:related:end -->
