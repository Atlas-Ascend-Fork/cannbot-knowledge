---
type: API
title: AscInt322Float
description: 根据mask将src中的int32_t类型数据转换为float类型，支持多种舍入模式，结果写入dst。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_type_convert/asc_int322float.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscInt322Float

根据mask将src中的每个int32_t类型数据转换成float类型，并支持多种舍入模式，结果写入dst。参考伪代码
关于舍入模式

参数：dst(输出): 目的操作数（矢量数据寄存器）。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 掩码寄存器，用于控制各元素是否参与计算。mask中与元素对应的比特位为1时，该元素参与计算；为0时，该元素不参与计算。

支持数据类型：float、int32_t。

约束：- src与dst的数据类型需要与函数原型匹配。
- 掩码位为0时，dst对应元素置0。
- 当int32_t的绝对值大于时，按函数后缀指定的舍入模式进行舍入。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscFloat2Int32](asc_float2int32.md)（`related`）：AscInt322Float 与《AscFloat2Int32》的实质衔接是：AscInt322Float 的 Vector 对应入口执行同一 int32→float 转换，AscFloat2Int32 则提供反向路径，用于核对舍入和 mask 置零契约。
- [AscInt642Float](asc_int642float.md)（`related`）：AscInt642Float 与《AscInt322Float》的实质衔接是：AscInt64ToFloat 的 Vector 对应入口、反向 FloatToInt64、其他整数宽度和 Int64ToInt32 共同解释 2:1 lane 分布及窄化/扩宽边界。
- [AscInt322float](../../vector_compute/asc_int322float.md)（`same_topic`）：AscInt322Float 与《AscInt322float》的实质衔接是：AscInt322Float 的 Vector 对应入口执行同一 int32→float 转换，AscFloat2Int32 则提供反向路径，用于核对舍入和 mask 置零契约。
<!-- cannbot:related:end -->
