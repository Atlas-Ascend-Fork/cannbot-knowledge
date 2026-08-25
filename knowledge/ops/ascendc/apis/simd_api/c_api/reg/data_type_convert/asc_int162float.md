---
type: API
title: AscInt162Float
description: 将src中int16_t类型的元素转换为float类型，并将结果写入dst。 由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int162float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt162Float

将src中int16_t类型的元素转换为float类型，并将结果写入dst。

由于源操作数与目的操作数类型位宽比为1:2，读取数据时需要将一个VL大小的数据分为两部分，根据不同接口选择输入数据索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、int16_t。

约束：mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscInt162float](../../vector_compute/asc_int162float.md)（`related`）：两卡都定义 int16→float 转换；Reg 版本还要求按奇偶半区处理 1:2 位宽展开，UB 版本提供 count 型连续转换，可据布局选择路径。
- [AscInt642Float](asc_int642float.md)（`same_topic`）：AscInt642Float 与《AscInt162Float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
<!-- cannbot:related:end -->
