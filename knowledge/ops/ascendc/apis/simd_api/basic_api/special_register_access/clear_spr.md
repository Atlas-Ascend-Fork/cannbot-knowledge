---
type: API
title: ClearSpr
description: 对指定的特殊寄存器进行清零操作。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/ClearSpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ClearSpr

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

对指定的特殊寄存器进行清零。当前支持表SpecialPurposeReg模板参数说明。

参数：spr: 特殊寄存器，类型为SpecialPurposeReg枚举类，具体的取值请参考表SpecialPurposeReg模板参数说明。

支持数据类型：无。

约束：本接口只能在VF函数外调用，命名空间为AscendC，函数标记符为__aicore__。如果需要在VF内调用，命名空间为AscendC::Reg，函数标记符为__simd_callee__，具体

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [ClearSpr](../reg_vector_compute/system_variable_access/clear_spr.md)（`related`）：两个 ClearSpr 分别面向 Reg VF 与普通 AI Core 调用域，文档明确需要按调用位置选择命名空间和函数标记。
- [GetSpr](get_spr.md)（`same_topic`）：焦点处理特殊寄存器 ClearSpr 的清零/读取配套操作；GetSpr正文界定“获取指定特殊寄存器的值，当前支持AR寄存器”。候选是另一 API 层的 ClearSpr、配套 GetSpr 或废弃清理接口，操作同一 SPR 状态。
- [asc_clear_ar_spr](../../c_api/reg/system_variables_access/asc_clear_ar_spr_deprecated.md)（`same_topic`）：焦点处理特殊寄存器 ClearSpr 的清零/读取配套操作；asc_clear_ar_spr正文界定“该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数”。候选是另一 API 层的 ClearSpr、配套 GetSpr 或废弃清理接口，操作同一 SPR 状态。
- [系统变量访问](../reg_vector_compute/system_variable_access/system_variable_access.md)（`same_topic`）：系统变量访问 与《ClearSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
<!-- cannbot:related:end -->
