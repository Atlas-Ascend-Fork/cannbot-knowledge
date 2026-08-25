---
type: API
title: ShiftRight
description: 对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/logical_compute/ShiftRight_shift_amount_tensor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# ShiftRight

对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。

本接口组包含 LocalTensor, LocalTensor。

本接口属于 UB 矢量计算逻辑运算接口。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [ShiftLeft](shift_left_shift_amount_tensor.md)（`related`）：相同 tensor 位移量输入下，ShiftLeft 执行相反方向，可用于方向选择和 round-trip 位测试。
- [AscShiftRight](../../../c_api/reg/logic_compute/asc_shiftright.md)（`same_topic`）：C Reg API 提供寄存器逐元素位移量版本，适合 RegBase 路径。
- [AscShiftright](../../../c_api/vector_compute/asc_shiftright.md)（`same_topic`）：AscShiftright：所选接口都执行右移，区别是 Memory/Reg/C API、逐元素 shift tensor 或 scalar shift；它们可直接核对位宽和移位量契约。 目标卡《ShiftRight》补充：对源操作数中的每个元素进行右移操作，右移位数由Tensor指定，无符号类型执行逻辑右移，有符号类型执行算术右移。
- [ShiftRight](shift_right.md)（`same_topic`）：基础 ShiftRight 的 tensor shift-amount 重载由本页展开；二者共享输出和整数类型约束。
- [ShiftRight](../../reg_vector_compute/logical_compute/shift_right.md)（`same_topic`）：RegTensor 版本完成相同逐元素右移，可按数据驻留位置选择。
<!-- cannbot:related:end -->
