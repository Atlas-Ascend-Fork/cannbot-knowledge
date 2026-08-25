---
type: API
title: AscFillValueConfig
description: fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。
tags: [task.lookup, topic.programming_model.development_mode.tensor_programming]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/struct/asc_fill_value_config.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AscFillValueConfig

asc_fill_value_config为fill_value的初始化参数结构体，包含asc_fill_l0a/asc_fill_l0b/asc_fill_l1接口需要配置的各种初始化参数。

字段：repeat：迭代次数，默认值：0。取值范围：[0, 32767]。；blk_num：每次迭代初始化的数据块个数，默认值：0。取值范围：[0, 32767]。 目的操作数位于L1 Buffer时，数据块大小是32B；目的操作数位于L0A Buffer/L0B Buffer时，数据块大小是512B。；dst_gap：目的操作数前一个迭代结束地址到后一个迭代起始地址之间的距离，默认值：0。取值范围：[0, 32767]。 目的操作数位于L1 Buffer时，单位是32B；目的操作数位于L0A Buffer/L0B Buffer时，单位是512B。

<!-- cannbot:related:start -->
## 相关

- [AscFillL0a](../cube_data_move/asc_fill_l0a.md)（`related`）：《AscFillL0a》明确“将标量值赋值给目的操作数，对L0A Buffer进行初始化。”；它与《AscFillValueConfig》的“fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscFillL0b](../cube_data_move/asc_fill_l0b.md)（`related`）：《AscFillL0b》明确“将标量值赋值给目的操作数，对L0B Buffer进行初始化。”；它与《AscFillValueConfig》的“fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。”在实际调用参数、数据流或结果校验上直接衔接。
- [AscFillL1](../cube_data_move/asc_fill_l1.md)（`related`）：《AscFillL1》明确“将标量值赋值给目的操作数，对L1 Buffer进行初始化。”；它与《AscFillValueConfig》的“fill_value的初始化参数结构体，包含fill_l0a、fill_l0b和fill_l1接口需要配置的初始化参数。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
