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

- [ClearSpr](../reg_vector_compute/system_variable_access/clear_spr.md)（`related`）：清零后可通过 GetSpr 读取特殊寄存器，用于验证状态复位或后续控制流消费。
- [ClearSpr](clear_spr.md)（`same_topic`）：焦点处理特殊寄存器 ClearSpr 的清零/读取配套操作；GetSpr正文界定“获取指定特殊寄存器的值，当前支持AR寄存器”。候选是另一 API 层的 ClearSpr、配套 GetSpr 或废弃清理接口，操作同一 SPR 状态。
- [GetCtrlSpr](get_ctrl_spr_isasi.md)（`same_topic`）：焦点处理特殊寄存器读取与配套清零、CTRL 位设置/复位；GetCtrlSpr正文说明“读取CTRL寄存器特定比特位上的值”。候选操作同一 SPR/CTRL 状态，明确读前设置、读后清理与位域复位。
- [ResetCtrlSpr](reset_ctrl_spr_isasi.md)（`same_topic`）：焦点处理特殊寄存器读取与配套清零、CTRL 位设置/复位；ResetCtrlSpr正文说明“对CTRL寄存器的特定比特位做重置，恢复为默认值”。候选操作同一 SPR/CTRL 状态，明确读前设置、读后清理与位域复位。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`same_topic`）：焦点处理特殊寄存器读取与配套清零、CTRL 位设置/复位；SetCtrlSpr正文说明“对CTRL寄存器的特定比特位进行设置，通过模板参数指定比特位范围并写入对应值”。候选操作同一 SPR/CTRL 状态，明确读前设置、读后清理与位域复位。
- [系统变量访问](../reg_vector_compute/system_variable_access/system_variable_access.md)（`same_topic`）：系统变量访问 与《GetSpr》的实质衔接是：本页的实际能力是 ClearSpr 清零 AR 特殊寄存器；GetSpr 读取同一 AR，而 Reg Squeeze 会把有效元素字节数写入 AR，因此它们形成明确的生产、读取和复位契约。
<!-- cannbot:related:end -->
