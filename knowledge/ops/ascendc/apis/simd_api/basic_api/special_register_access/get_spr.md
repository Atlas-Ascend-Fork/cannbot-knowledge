---
type: API
title: GetSpr
description: 获取指定特殊寄存器的值，当前支持AR寄存器。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/GetSpr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# GetSpr

头文件路径为："basic_api/kernel_operator_sys_var_intf.h"。

获取指定特殊寄存器的值。当前支持表SpecialPurposeReg模板参数说明。

参数：spr: 特殊寄存器，类型为SpecialPurposeReg枚举类，具体的取值请参考表SpecialPurposeReg模板参数说明。；AR: AR寄存器通常配合Reg矢量计算API Squeeze和连续非对齐搬出的场景3（无需显式传入偏移量）接口一起使用，寄存器会存储有效元素的总字节数。

支持数据类型：接口返回数据类型为int64_t。

约束：本接口只能在VF函数外调用，命名空间为AscendC，函数标记符为__aicore__。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Squeeze](../reg_vector_compute/compare_and_select/squeeze.md)（`related`）：“参数：spr: 特殊寄存器，类型为SpecialPurposeReg枚举类，具体的取值请参考表SpecialPurposeReg模板参数说明。；AR: AR寄存器通常配合Reg矢量计算API Squeeze和连续非对齐搬出的场景3（无需显式传入偏移量）接口一起使用，寄存器会存储有效元素的总字节数。”与“特别地，当模板参数store取值为GatherMaskMode::STORE_REG时，Squeeze会将有效元素的总字节数存入AR特殊寄存器。此时配合使用连续非对齐搬出的场景3接口（无需显式传入偏移量），StoreUnAlign会自动从AR寄存器读取有效字节数作为地址偏移，参考调用示例。”提供双方正文证据。GetSpr 读取的 AR 值正是 Squeeze 在 STORE_REG 模式写入的有效元素总字节数，形成特殊寄存器生产与读取关系。
<!-- cannbot:related:end -->
