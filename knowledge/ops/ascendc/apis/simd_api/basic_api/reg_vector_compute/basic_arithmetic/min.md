---
type: API
title: Min
description: 根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/basic_arithmetic/Min.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# Min

根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。

RegTensor寄存器是矢量计算基本单元，RegTensor位宽为VL（Vector Length），长度为256B。b64或complex32类型下，支持通过RegTrait模板参数扩展存储2VL用于复杂计算。

本接口组包含 MaskMergeMode, RegTensor, RegTensor, RegTensor, MaskReg。

本接口属于 Reg 矢量计算基础算术接口，操作 RegTensor 寄存器数据，直接在寄存器级别执行矢量运算。

支持的数据类型为 b8、b16、b32、b64。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：RegTensor寄存器数量上限为32。超出限制上限的寄存器数据会写入预留的8KUB内存中，可能会引起性能劣化。编译器会自动复用生命周期结束的寄存器和预留内存，若寄存器与预留内存均存在可用空间，将优先复用寄存器。；寄存器的生命周期限定于单个VF内部。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [AscMin](../../../c_api/vector_compute/asc_min.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《AscMin》说明asc_min（矢量计算）。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [Clamp（数学计算）](../../../adv_api/math_compute/clamp_interface/clamp.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [Max](max.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Max》说明根据mask对源操作数srcReg0、srcReg1按元素求最大值，将结果写入目的操作数dstReg。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [Mins](mins.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Mins》说明根据mask对源操作数srcReg按元素与标量比较取较小值，将结果写入目的操作数dstReg。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [min（整数数学函数）](../../../../simt_api/math_functions/integer_math_functions/min.md)（`related`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《min（整数数学函数）》说明获取两个输入数据中的最小值。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [AscMin](../../../c_api/reg/arithmetic_compute/asc_min.md)（`same_topic`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《AscMin》说明根据mask对源操作数src0、src1按元素求最小值，将结果写入目的操作数dst。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
- [Min](../../memory_vector_compute/basic_arithmetic/min.md)（`same_topic`）：《Min》说明根据mask对源操作数srcReg0、srcReg1按元素求最小值，将结果写入目的操作数dstReg。；《Min》说明双目矢量计算接口，对两个输入tensor按元素取最小值。。二者在Reg Min与Max、标量Mins及Memory/C/SIMT等价接口的操作数形态不同，Clamp则直接组合最小/最大边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
