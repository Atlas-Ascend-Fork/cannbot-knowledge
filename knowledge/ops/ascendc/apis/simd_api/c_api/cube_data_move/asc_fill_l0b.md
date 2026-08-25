---
type: API
title: AscFillL0b
description: 将标量值赋值给目的操作数，对L0B Buffer进行初始化。
tags: [task.lookup, topic.data_movement.data_copy]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/cube_data_move/asc_fill_l0b.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---
# AscFillL0b

将value的二进制值赋值给dst，对L0B Buffer的Local Memory进行初始化。

参数：dst(输出): 目的操作数（矩阵）的起始地址。；value(输入): 源操作数（标量）。；config(输入): 使用的初始化相关参数，详细说明请参考asc_fill_value_config。

约束：- 各存储单元的空间大小和对齐要求
- 操作数地址重叠约束
- 若dst和value的数据类型不相同，则需要根据dst的数据类型对value的值进行转换，具体

仅 Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFillL0a](asc_fill_l0a.md)（`related`）：《AscFillL0a》明确“将标量值赋值给目的操作数，对L0A Buffer进行初始化。”；它与《AscFillL0b》的“将标量值赋值给目的操作数，对L0B Buffer进行初始化。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscFillL1](asc_fill_l1.md)（`related`）：《AscFillL1》明确“将标量值赋值给目的操作数，对L1 Buffer进行初始化。”；它与《AscFillL0b》的“将标量值赋值给目的操作数，对L0B Buffer进行初始化。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscFillValueConfig](../struct/asc_fill_value_config.md)（`related`）：《AscFillL0b》明确“将标量值赋值给目的操作数，对L0B Buffer进行初始化。”；它与《AscFillValueConfig》的“fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
