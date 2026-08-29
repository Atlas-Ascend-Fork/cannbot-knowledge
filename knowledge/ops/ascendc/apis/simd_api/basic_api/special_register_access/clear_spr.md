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
