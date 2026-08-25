---
type: API
title: 系统变量访问
description: 寄存器侧系统变量访问类接口汇总，提供squeeze_and_storeunalign_init初始化及已废弃的clear_ar_spr等能力。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/system_variables_access/system_variables_access.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# 系统变量访问（C API）

系统变量访问接口集合，用于访问和设置AI Core内部的系统变量寄存器。包含asc_squeeze_and_storeunalign_init（非对齐存储初始化接口，用于配置非对齐数据搬运的参数）和asc_clear_ar_spr（废弃接口，原用于清除AR/SPR寄存器，已被新机制替代）。系统变量寄存器控制计算和搬运的行为模式，正确配置系统变量是使用高维切分计算等高级功能的前提。

<!-- cannbot:related:start -->
## 相关

- [asc_clear_ar_spr](asc_clear_ar_spr_deprecated.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“系统变量访问”定义：寄存器侧系统变量访问类接口汇总，提供squeeze_and_storeunalign_init初始化及已废弃的clear_ar_spr等能力。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
<!-- cannbot:related:end -->
