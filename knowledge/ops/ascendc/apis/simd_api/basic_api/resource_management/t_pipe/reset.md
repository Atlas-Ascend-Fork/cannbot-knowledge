---
type: API
title: Reset
description: 完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.memory_management]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Reset.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---
# Reset

头文件路径为："basic_api/kernel_tpipe.h"。

完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。

针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL[48]保持原值，CTRL[60]复位为1。CTRL寄存器比特位说明请见SetCtrlSpr。

仅 Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 训练系列产品、Kirin X90、Kirin 9030 支持。

<!-- cannbot:related:start -->
## 相关

- [Init](init.md)（`related`）：完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。；用于内存和同步流水事件EventID的初始化。；Reset 释放当前资源并恢复 Init 建立的内存与 EventID 状态，两接口构成 TPipe 资源生命周期。
- [SetCtrlSpr](../../special_register_access/set_ctrl_spr_isasi.md)（`related`）：针对Ascend 950PR/Ascend 950DT，调用该接口后，CTRL［48］保持原值，CTRL［60］复位为1。CTRL寄存器比特位说明请见SetCtrlSpr。；对CTRL寄存器（控制寄存器）的特定比特位进行设置。通过模板参数startBit和endBit指定目标比特位范围，将运行参数value（超出比特位范围会出现编译报错）写入CTRL寄存器对应位置。；焦点给出 Reset 对 CTRL 位的副作用，目标提供这些位的显式读取边界与恢复设置入口。
<!-- cannbot:related:end -->
