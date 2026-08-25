---
type: API
title: AscGetCmpMask
description: 此接口用于获取Compare操作的比较结果。
tags: [task.lookup, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/vector_compute/asc_get_cmp_mask.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [a2, a3]
---

# AscGetCmpMask

此接口用于获取Compare操作的比较结果。
函数原型：void asc_get_cmp_mask(__ubuf__ void* dst)
参数：dst（输出）：存放比较操作结果的地址。
约束：需和Compare操作配合使用。
支持平台：Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品；不支持：Ascend 950PR/Ascend 950DT, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core等

<!-- cannbot:related:start -->
## 相关

- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《AscGetCmpMask》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [AscLe](asc_le.md)（`related`）：当 AscLe 把结果留在比较寄存器时，必须用 asc_get_cmp_mask 取出比较位，正文明确这一消费步骤。
- [AscNe](asc_ne.md)（`related`）：《AscNe》说明按元素判断src0 != src1是否成立，若成立则输出结果为1，否则为0。每个元素的比较结果占1个bit。 当结果输出到寄存器中时，可在计算完成后调用asc_get_cmp_mask获取比较结果。；《AscGetCmpMask》说明此接口用于获取Compare操作的比较结果。。二者在AscNe生成1-bit比较结果并通过CMPMASK读取；Reg等价接口、标量变体和Eq/Gt边界用于确认谓词语义上存在可执行的直接衔接。
- [AscSetCmpMask](asc_set_cmp_mask.md)（`related`）：AscGetCmpMask说明此接口用于获取Compare操作的比较结果；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [GetCmpMask](../../basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`same_topic`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《AscGetCmpMask》明确提供“此接口用于获取Compare操作的比较结果。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
<!-- cannbot:related:end -->
