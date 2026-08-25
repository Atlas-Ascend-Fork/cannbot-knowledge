---
type: API
title: AscInt642Float
description: 将int64_t类型数据转换为float，支持多种舍入模式，源操作数与目的操作数位宽比为2:1。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int642float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt642Float

将int64_t类型数据转换为float，并支持多种舍入模式。

关于舍入模式
由于源操作数与目的操作数类型位宽比为2:1，写入数据时需要将一个VL大小的数据分为两部分，根据不同接口选择数据写入索引为奇数的位置或偶数的位置。

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。mask未筛选的元素在输出中置零。

支持数据类型：float、int64_t。

约束：- mask控制源操作数是否参与计算，源操作数不参与计算的元素在输出对应位置置零。
- 当数据写入目的操作数索引为奇数的位置，索引为偶数位置的数值置零。反之亦然。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int64](asc_float2int64.md)（`related`）：AscInt642Float 与《AscFloat2Int64》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt322Float](asc_int322float.md)（`related`）：AscInt642Float 与《AscInt322Float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt642float](../../vector_compute/asc_int642float.md)（`related`）：AscInt642Float 与《AscInt642float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt642int32](asc_int642int32.md)（`related`）：《AscInt642int32》说明将int64_t类型源操作数转换为int32_t类型，支持饱和与非饱和模式。；《AscInt642Float》说明将int64_t类型数据转换为float，支持多种舍入模式，源操作数与目的操作数位宽比为2:1。。二者在int64到int32窄化的饱和/非饱和语义需与反向扩宽及同源转换对照验证上存在可执行的直接衔接。
- [AscInt642int32](../../vector_compute/asc_int642int32.md)（`related`）：AscInt642Float 与《AscInt642int32》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt162Float](asc_int162float.md)（`same_topic`）：AscInt642Float 与《AscInt162Float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
<!-- cannbot:related:end -->
