---
type: API
title: asc_get_ar_spr (废弃)
description: 该接口已废弃，请使用asc_get_squeeze_status实现此功能。 读取指定特殊寄存器的值。
tags: [task.lookup, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sys_var/asc_get_ar_spr_deprecated.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# asc_get_ar_spr (废弃)

该接口已废弃，请使用asc_get_squeeze_status实现此功能。 读取指定特殊寄存器的值。
函数原型：int64_t asc_get_ar_spr()
返回值：返回int64_t类型的特殊寄存器中的数值。
支持平台：Ascend 950PR/Ascend 950DT；不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品等

<!-- cannbot:related:start -->
## 相关

- [废弃接口](../../../appendix/deprecated_interface.md)（`related`）：asc_get_ar_spr (废弃) 与《废弃接口》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
- [AscGetSqueezeStatus](asc_get_squeeze_status.md)（`same_topic`）：废弃 asc_get_ar_spr 卡明确要求改用 AscGetSqueezeStatus；两者都读取 squeeze 操作写入 AR 的有效数据长度，后者是当前接口。
- [AscSqueezeV2](../reg/compare_and_select/asc_squeeze_deprecated.md)（`same_topic`）：asc_get_ar_spr (废弃) 与《AscSqueezeV2》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
- [AscSqueezeWithStatus](../reg/compare_and_select/asc_squeeze_with_status_deprecated.md)（`same_topic`）：asc_get_ar_spr (废弃) 与《AscSqueezeWithStatus》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
- [asc_clear_ar_spr](../reg/system_variables_access/asc_clear_ar_spr_deprecated.md)（`same_topic`）：asc_get_ar_spr (废弃) 与《asc_clear_ar_spr》的实质衔接是：asc_get_ar_spr 已明确由 AscGetSqueezeStatus 替代；clear AR、旧 SqueezeWithStatus/SqueezeV2 和废弃接口表解释该特殊寄存器状态的生产、清理与迁移。
<!-- cannbot:related:end -->
