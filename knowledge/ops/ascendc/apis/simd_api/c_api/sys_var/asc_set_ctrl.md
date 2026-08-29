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

- [AscGetCtrl](asc_get_ctrl.md)（`related`）：读取CTRL寄存器（控制寄存器）特定比特位上的值。；约束：使用前需要先用asc_get_ctrl()获取当前值，仅对需要变更的bit位进行修改。；仅支持已设置CTRL［48］、CTRL［53］、CTRL［56］、CTRL［59］比特位。；SetCtrl 的约束要求先由 GetCtrl 读取现值并只修改目标位，因此读取与设置形成寄存器安全更新序列。
<!-- cannbot:related:end -->
