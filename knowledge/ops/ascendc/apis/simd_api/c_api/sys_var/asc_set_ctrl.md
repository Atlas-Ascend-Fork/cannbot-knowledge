---
type: API
title: AscSetCtrl
description: 对CTRL寄存器特定比特位进行设置。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_set_ctrl.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# AscSetCtrl

对CTRL寄存器（控制寄存器）的特定比特位进行设置。
函数原型：void asc_set_ctrl(uint64_t config)
参数：config（输入）：待设置的寄存器值。常用CTRL寄存器比特位说明参考表2。
约束：使用前需要先用asc_get_ctrl()获取当前值，仅对需要变更的bit位进行修改。；仅支持已设置CTRL[48]、CTRL[53]、CTRL[56]、CTRL[59]比特位。
支持平台：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core, Atlas 推理系列产品Vector Core等

<!-- cannbot:related:start -->
## 相关

- [GetCtrlSpr](../../basic_api/special_register_access/get_ctrl_spr_isasi.md)（`related`）：AscSetCtrl 是 C API 配置 CTRL 的对应入口，便于在 C 路线复现 Set/Get 验证。
- [SetCtrlSpr](../../basic_api/special_register_access/set_ctrl_spr_isasi.md)（`related`）：SetCtrlSpr 以模板位段方式写 CTRL 寄存器，AscSetCtrl 则写入读取并修改后的整体寄存器值，是同一控制寄存器的两种配置入口。
- [系统变量](system_variables.md)（`related`）：系统变量入口页把 asc_set_ctrl/get_ctrl 放在运行时状态配置接口中，并列出其与核编号、架构和搬运寄存器的边界。
- [AscGetCtrl](asc_get_ctrl.md)（`same_topic`）：AscGetCtrl 与《AscSetCtrl》的实质衔接是：AscGetCtrl 必须与 AscSetCtrl 配对做读改写，Get/Set/ResetCtrlSpr 与系统变量说明 CTRL 控制位的读取、保存和恢复范围。
<!-- cannbot:related:end -->
