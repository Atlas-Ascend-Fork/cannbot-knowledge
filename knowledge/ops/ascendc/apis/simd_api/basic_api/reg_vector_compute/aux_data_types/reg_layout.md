---
type: API
title: RegLayout
description: 源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。更多特性说明请参考Cast。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/aux_data_types/RegLayout.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# RegLayout

源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。更多特性说明请参考Cast。

头文件路径："basic_api/reg_compute/kernel_reg_compute_vec_vconv_intf.h"。 Cast用于数据类型精度转换，将源操作数数据类型转换成目的操作数数据类型，能够实现浮点转整数、浮点转浮点、整数转浮点、整数转整数的数据类型转换。转换过程中，由于位宽变化、精度变化，支持配置如下参数进行功能实现： - RegLayout：源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。 - SatMode：用于设置饱和与不饱和模式。 - MaskMergeMode：用于指定写入寄存器数据模式，mask未选择的元素在dst中置零或保留dst原值。 - RoundMode：用于设置舍入模式。 不同数据类型下元素对应的mask位宽不一致，在Cast进行类型转换时，MaskReg根据输

本接口组包含 Cast。

本接口属于 Reg 矢量计算辅助数据类型定义。

约束：当目的操作数位宽比源操作数小时，再MaskReg和RegLayout作用下，目的操作数中的无效元素均为0。；该指令需配合SetCtrlSpr指令使用，通过设置寄存器的值控制Cast的不饱和模式和饱和模式。；舍入模式仅在可能导致精度损失且支持该舍入模式的转换中生效，具体支持情况请参考关键特性说明。；不同类型转换的不饱和与饱和模式的描述有所区别，全局或单指令生效配置方法也不同，具体内容参考表4 不同类型转换场景的不饱和模式和饱和模式、表5 饱和模式全局或单指令生效配置表。

支持的硬件型号：Ascend 950PR/Ascend 950DT。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换](../../../../../runbooks/precision/b16_reg_cast_layout_should_convert_at_localtensor_boundary.md)（`exemplifies`）：特定 b16 load-cast-store 组合失真时在 LocalTensor 边界转换 与《RegLayout》的实质衔接是：故障链是 B16 LoadDist 解包后 Reg::Cast 写 UB 的 lane 布局失真；UNPACK 数值转换卡和 RegLayout 解释机制，LocalTensor/Load/Store 是出入边界，正确配方改用 Memory Cast 在 LocalTensor 边界转换。
- [Cast](../type_conversion/cast.md)（`related`）：《Cast》说明Reg矢量计算的精度转换接口，支持浮点转整数、浮点转浮点、整数转浮点和整数转整数四种类型转换。；《RegLayout》说明源操作数和目的操作数位宽不同时，单条指令计算量以位宽更大的数据类型为准，RegLayout用于控制位宽小的元素在寄存器中的排布方式。更多特性说明请参考Cast。。二者在Reg Cast的源目类型布局、舍入、饱和及mask trait必须共同匹配，相关编译和NaN故障是这些配置错误的直接验证上存在可执行的直接衔接。
<!-- cannbot:related:end -->
