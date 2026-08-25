---
type: API
title: AscSetCmpMask
description: 为asc_select操作设置作用于选择的Mask掩码。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_set_cmp_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscSetCmpMask

为asc_select操作设置作用于选择的Mask掩码。
函数原型：void asc_set_cmp_mask(__ubuf__ void* sel_mask)
参数：sel_mask（输入）：用于选择的Mask掩码的起始地址。
约束：需和asc_select操作配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败说明arch35 Select(VSEL_CMPMASK_SPR) cmpmask SPR 跨调用残留致分支错乱；case 单独 PASS、套件内 FAIL 为判别信号；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [AscGetCmpMask](asc_get_cmp_mask.md)（`related`）：AscGetCmpMask说明此接口用于获取Compare操作的比较结果；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [AscSelect](../reg/compare_and_select/asc_select.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《AscSetCmpMask》补充：为asc_select操作设置作用于选择的Mask掩码。
- [AscSelect](asc_select.md)（`related`）：AscSelect说明执行矢量选择操作，给定两个源操作数src0和src1，根据条件选择元素，得到目的操作数dst。此接口配合asc_set_cmp_mask(sel_mask)设置，规则为：当sel_mask的比特位是1时，从src0选取；当比特位是0时，从src1选择；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [GetCmpMask](../../basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`related`）：GetCmpMask说明获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [Select](../../basic_api/reg_vector_compute/mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《AscSetCmpMask》具体提供“为asc_select操作设置作用于选择的Mask掩码。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
<!-- cannbot:related:end -->
