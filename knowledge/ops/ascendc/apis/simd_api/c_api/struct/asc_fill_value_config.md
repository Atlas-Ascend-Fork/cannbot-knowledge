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

- [AscFillL0a](../cube_data_move/asc_fill_l0a.md)（`related`）：“config(输入): 使用的初始化相关参数，详细说明请参考asc_fill_value_config”与“asc_fill_value_config为fill_value的初始化参数结构体”把 AscFillL0a 的 config 形参连接到 repeat、blk_num 与 dst_gap 的结构体契约。
- [AscFillL0b](../cube_data_move/asc_fill_l0b.md)（`related`）：asc_fill_value_config为fill_value的初始化参数结构体，包含asc_fill_l0a/asc_fill_l0b/asc_fill_l1接口需要配置的各种初始化参数。；config(输入): 使用的初始化相关参数，详细说明请参考asc_fill_value_config。；结构体字段直接作为 asc_fill_l0b 初始化 L0B 的配置输入。
- [AscFillL1](../cube_data_move/asc_fill_l1.md)（`related`）：asc_fill_value_config为fill_value的初始化参数结构体，包含asc_fill_l0a/asc_fill_l0b/asc_fill_l1接口需要配置的各种初始化参数。；config(输入): 使用的初始化相关参数，详细说明请参考asc_fill_value_config。；结构体字段直接作为 asc_fill_l1 初始化 L1 的配置输入。
<!-- cannbot:related:end -->
