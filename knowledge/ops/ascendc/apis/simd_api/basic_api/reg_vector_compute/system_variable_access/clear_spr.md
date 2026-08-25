---
type: API
title: ClearSpr
description: 对指定的特殊目的寄存器进行清零操作，通过模板参数指定目标特殊寄存器，调用后该寄存器值被置为0。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/system_variable_access/ClearSpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ClearSpr

头文件路径为："basic_api/reg_compute/kernel_reg_compute_gather_mask_intf.h"。

该接口用于对指定的特殊目的寄存器（SpecialPurposeReg）进行清零操作。通过模板参数spr指定目标特殊寄存器，调用后该寄存器的值被置为0，当前支持的特殊寄存器见表 SpecialPurposeReg模板参数说明。

参数：spr: 特殊寄存器，类型为SpecialPurposeReg枚举类。具体的取值请参考表 SpecialPurposeReg模板参数说明。；AR: 一个特殊的地址寄存器，通常配合SqueezeReg矢量计算API一起使用，SqueezeReg矢量计算API会存储有效元素的总字节数到AR寄存器。

约束：本接口只能在VF函数内调用，命名空间为AscendC::Reg，函数标记符为__simd_callee__。如果需要在VF外调用，命名空间为AscendC，函数标记符为__aicore__，具体

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ClearSpr](../../special_register_access/clear_spr.md)（`related`）：两个 ClearSpr 分别面向 Reg VF 与普通 AI Core 调用域，文档明确需要按调用位置选择命名空间和函数标记。
- [GetSpr](../../special_register_access/get_spr.md)（`related`）：清零后可通过 GetSpr 读取特殊寄存器，用于验证状态复位或后续控制流消费。
- [系统变量访问](system_variable_access.md)（`same_topic`）：系统变量访问 与《ClearSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
<!-- cannbot:related:end -->
