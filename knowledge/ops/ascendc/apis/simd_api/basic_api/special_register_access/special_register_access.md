---
type: API
title: 特殊寄存器访问
description: 特殊寄存器访问接口索引页，包含GetSpr、ClearSpr及SetCtrlSpr/GetCtrlSpr等控制与饱和度标志接口(ISASI)。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/special_register_access/special_register_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 特殊寄存器访问

提供特殊寄存器（SPR）的读取与清除接口GetSpr/ClearSpr，以及控制类寄存器操作SetCtrlSpr/GetCtrlSpr/ResetCtrlSpr(ISASI)。
另含饱和度标志位管理接口GetSaturationFlag/SetSaturationFlag(ISASI)，用于查询和设置计算过程中的饱和溢出状态。ISASI标记的接口为内联汇编风格接口。
