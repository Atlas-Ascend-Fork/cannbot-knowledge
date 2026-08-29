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

- [GetCtrlSpr](get_ctrl_spr_isasi.md)（`related`）：“读取CTRL寄存器（控制寄存器）特定比特位上的值。”；“对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数［startBit, endBit］指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。”。Reset 后可用 GetCtrlSpr 对同一 bit range 回读默认值，闭合临时控制位的恢复验证。
- [SetCtrlSpr](set_ctrl_spr_isasi.md)（`same_topic`）：“对CTRL寄存器（控制寄存器）的特定比特位做重置。由模板参数［startBit, endBit］指定的比特位重置为默认值，默认值参考表 常用CTRL寄存器比特位说明。”与“对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。”提供双方正文证据。SetCtrlSpr 写指定 CTRL 位段，ResetCtrlSpr 将同一位段恢复默认值，构成控制寄存器配置与清理的生命周期闭环。
<!-- cannbot:related:end -->
