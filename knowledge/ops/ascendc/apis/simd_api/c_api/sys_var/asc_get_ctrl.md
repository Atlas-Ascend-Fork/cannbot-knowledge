---
type: API
title: AscGetCtrl
description: 读取CTRL寄存器特定比特位上的值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_ctrl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscGetCtrl

读取CTRL寄存器（控制寄存器）特定比特位上的值。
函数原型：int64_t asc_get_ctrl()
返回值：CTRL寄存器的值。具体含义请参考asc_set_ctrl中的描述。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [GetCtrlSpr](../../basic_api/special_register_access/get_ctrl_spr_isasi.md)（`related`）：AscGetCtrl 与《GetCtrlSpr》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [ResetCtrlSpr](../../basic_api/special_register_access/reset_ctrl_spr_isasi.md)（`related`）：AscGetCtrl 与《ResetCtrlSpr》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [SetCtrlSpr](../../basic_api/special_register_access/set_ctrl_spr_isasi.md)（`related`）：AscGetCtrl 与《SetCtrlSpr》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [AscSetCtrl](asc_set_ctrl.md)（`same_topic`）：AscGetCtrl 与《AscSetCtrl》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
- [系统变量](system_variables.md)（`same_topic`）：AscGetCtrl 与《系统变量》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
<!-- cannbot:related:end -->
