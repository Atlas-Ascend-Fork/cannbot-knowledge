---
type: API
title: AscDuplicateMerge
description: merge模式下将src的最低位元素广播到dst中被mask筛选的位置，未被筛选的元素保留原值。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/data_fill/asc_duplicate_merge.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# AscDuplicateMerge

merge模式下，将src的最低位元素广播到dst中被mask筛选的位置，dst中未被mask筛选的元素保留原值。

参数：dst(输入/输出): 目的操作数（矢量数据寄存器）。merge模式下，未被mask筛选的元素保留原值。；src(输入): 源操作数（矢量数据寄存器）。；mask(输入): 源操作数掩码（掩码寄存器），用于指示在计算过程中哪些元素参与计算。对应位置为1时参与计算，为0时不参与计算。

支持数据类型：bfloat16_t、float、fp8_e4m3fn_t、fp8_e5m2_t、fp8_e8m0_t、half、int16_t、int32_t、int8_t、uint16_t、uint32_t、uint8_t。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 广播枚举与模板顺序不兼容](../../../../../runbooks/compilation/reg_duplicate_highlow_precedes_merge_mode.md)（`exemplifies`）：merge模式下，将src的最低位元素广播到dst中被mask筛选的位置，dst中未被mask筛选的元素保留原值。；安装头文件的真实声明表明，寄存器到寄存器重载的模板形参依次是 `T, HighLowPart pos, MaskMergeMode mode`。。API定义 merge 广播最低位并保留未命中 lane，Runbook给出 CANN 9.0.1 调用该寄存器广播重载时的模板参数次序。
<!-- cannbot:related:end -->
