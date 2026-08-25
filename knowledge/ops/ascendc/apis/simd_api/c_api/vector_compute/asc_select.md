---
type: API
title: AscSelect
description: 执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [a2, a3]
---

# AscSelect

执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择。
函数原型：void asc_select(__ubuf__ half* dst, __ubuf__ half* src0, __ubuf__ half* src1, uint32_t count)
约束：需要配合asc_set_cmp_mask接口使用。；dst、src0、src1的起始地址需要32字节对齐；操作数地址重叠约束请参考通用地址重叠约束。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：该 runbook 记录 CMPMASK SPR 跨调用泄漏引发非确定错选，直接验证 AscSelect 对外部 mask 状态的依赖。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：该 runbook 说明异步 SIMT 生产选择条件而未正确同步时，AscSelect 会消费旧 mask 并错选分支。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../../../../runbooks/compilation/arch35_select_32b_507035.md)（`exemplifies`）：该 runbook 展示 AscSelect 分块时 mask 偏移非 32B 对齐导致 507035，补充接口卡未展开的地址约束故障。
- [AscSelect](../reg/compare_and_select/asc_select.md)（`related`）：Reg AscSelect 实现同类条件选择但使用寄存器数据与 mask，可按 UB Vector 或 Reg 路线选型。
- [AscSetCmpMask](asc_set_cmp_mask.md)（`related`）：AscSelect说明执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
<!-- cannbot:related:end -->
