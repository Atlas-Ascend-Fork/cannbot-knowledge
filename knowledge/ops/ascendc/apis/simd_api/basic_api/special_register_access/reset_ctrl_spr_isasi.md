---
type: API
title: ResetCtrlSpr
description: 对CTRL寄存器的特定比特位做重置，恢复为默认值。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/ResetCtrlSpr_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# ResetCtrlSpr

头文件路径为："basic_api/kernel_operator_common_intf.h"。

对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数[startBit, endBit]指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。

参数：startBit: 起始比特位索引。；endBit: 终止比特位索引。

支持数据类型：本接口为寄存器访问接口，不涉及张量数据类型操作。

约束：仅支持CTRL[8:6]、CTRL[10:9]、CTRL[48]、CTRL[50]、CTRL[53]、CTRL[59]、CTRL[60]比特位，各比特位的说明

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [AscGetCtrl](../../c_api/sys_var/asc_get_ctrl.md)（`related`）：AscGetCtrl 与《ResetCtrlSpr》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [SetSaturationFlag](set_saturation_flag_isasi.md)（`related`）：“SetSaturationFlag”定义：设置饱和开关的标志位，控制计算或精度转换时饱和模式的开启与关闭。；“ResetCtrlSpr”定义：对CTRL寄存器的特定比特位做重置，恢复为默认值。。实质衔接：SetSaturationFlag 修改饱和状态，Get 用于验证当前值；通用 CTRL SPR set/reset 提供底层控制位管理和恢复默认值的契约。
- [GetCtrlSpr](get_ctrl_spr_isasi.md)（`same_topic`）：ResetCtrlSpr 恢复 CTRL 位段，避免临时控制配置泄漏到后续计算。
- [GetSpr](get_spr.md)（`same_topic`）：焦点处理特殊寄存器读取与配套清零、CTRL 位设置/复位；ResetCtrlSpr正文说明“对CTRL寄存器的特定比特位做重置，恢复为默认值”。候选操作同一 SPR/CTRL 状态，明确读前设置、读后清理与位域复位。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`same_topic`）：SetCtrlSpr 临时修改 CTRL 位段，ResetCtrlSpr 是对应的收尾接口。
<!-- cannbot:related:end -->
