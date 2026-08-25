---
type: API
title: asc_clear_ar_spr
description: 该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/system_variables_access/asc_clear_ar_spr_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_clear_ar_spr

该接口已废弃。请使用asc_squeeze_and_storeunalign_init实现此功能。 对AR特殊寄存器进行清零操作。AR寄存器用于配合asc_squeeze_with_status使用：当调用asc_squeeze_with_status时，有效元素的总字节数会被存入AR寄存器。在调用asc_squeeze_with_status之前，需调用该接口将AR寄存器清零。
函数原型：void asc_clear_ar_spr()
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [AscSqueezeAndStoreunalignInit](asc_squeeze_and_storeunalign_init.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“AscSqueezeAndStoreunalignInit”定义：对AR特殊寄存器清零，用于配合asc_squeeze_and_storeunalign进行地址自动偏移，首次调用前需初始化。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [AscSqueezeWithStatus](../compare_and_select/asc_squeeze_with_status_deprecated.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“AscSqueezeWithStatus”定义：已废弃接口，请使用asc_squeeze_and_storeunalign。将src中被mask选择的有效元素依次复制到dst并连续排列，会将有效数据大小保存至AR寄存器供搬出时使用。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [废弃接口](../../../../appendix/deprecated_interface.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“废弃接口”定义：列出Ascend C中已废弃或后续版本将废弃的C API接口，并给出每个接口的推荐替代方案。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [系统变量访问](system_variables_access.md)（`related`）：“asc_clear_ar_spr”定义：该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数。；“系统变量访问”定义：寄存器侧系统变量访问类接口汇总，提供squeeze_and_storeunalign_init初始化及已废弃的clear_ar_spr等能力。。实质衔接：废弃 clear AR SPR 的直接替代是 SqueezeAndStoreUnalignInit；旧 SqueezeWithStatus 解释 AR 有效字节计数的消费链，附录用于查替换。
- [ClearSpr](../../../basic_api/special_register_access/clear_spr.md)（`same_topic`）：焦点处理特殊寄存器 ClearSpr 的清零/读取配套操作；asc_clear_ar_spr正文界定“该接口已废弃，请使用asc_squeeze_and_storeunalign_init替代。用于对AR特殊寄存器清零，配合asc_squeeze_with_status记录有效元素字节数”。候选是另一 API 层的 ClearSpr、配套 GetSpr 或废弃清理接口，操作同一 SPR 状态。
- [asc_get_ar_spr (废弃)](../../sys_var/asc_get_ar_spr_deprecated.md)（`same_topic`）：asc_get_ar_spr (废弃) 与《asc_clear_ar_spr》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
<!-- cannbot:related:end -->
