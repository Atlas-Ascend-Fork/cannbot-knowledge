---
type: API
title: SetCmpMask
description: 设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/SetCmpMask_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# SetCmpMask(ISASI)

## 产品支持情况

- Ascend 950PR/Ascend 950DT：支持

- Atlas A3 训练系列产品/Atlas A3 推理系列产品：支持

- Atlas A2 训练系列产品/Atlas A2 推理系列产品：支持

- Atlas 200I/500 A2 推理产品：不支持

- Atlas 推理系列产品 AI Core：支持

- Atlas 推理系列产品 Vector Core：不支持

- Atlas 训练系列产品：不支持

## 功能说明

头文件路径为：`"basic_api/kernel_operator_vec_cmpsel_intf.h"`。

设置比较寄存器的值，配合不传入mask参数的Select接口使用，根据不同的selMode传入不同的数据。

- 模式0（SELMODE::VSEL_CMPMASK_SPR）

    SetCmpMask中传入selMask LocalTensor。

- 模式1（SELMODE::VSEL_TENSOR_SCALAR_MODE）

    SetCmpMask中传入src1 LocalTensor。

- 模式2（SELMODE::VSEL_TENSOR_TENSOR_MODE）

    SetCmpMask中传入LocalTensor，LocalTensor中存放的是selMask的地址。

## 函数原型

## 参数说明

**表1**  模板参数说明

**表2**  参数说明

## 数据类型

支持数据类型为：b8、b16、b32、b64。

## 返回值说明

无

## 约束说明

无

## 调用示例

- 当selMode为模式0或模式2时：



- 当selMode为模式1时：

<!-- cannbot:related:start -->
## 相关

- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：SetCmpMask 接口说明 mask 被装入比较寄存器供不显式传 mask 的 Select 使用，正是本卡 CMPMASK_SPR repeat 复用的寄存器边界。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“SetCmpMask”定义：设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：VselIntrinsicsImpl 每 repeat 调 set_cmpmask(sel)，接口说明从地址装载 cmpmask。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《SetCmpMask》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《SetCmpMask》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../../../../../runbooks/compilation/arch35_select_32b_507035.md)（`exemplifies`）：该 Runbook 实测 SetCmpMask/Select 路径若掩码地址未满足 32B 要求会触发 507035，并给出对齐探针。
- [AscSelect](../../../c_api/reg/compare_and_select/asc_select.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《SetCmpMask》补充：设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
- [CompareStoreToRegister](compare_store_to_register.md)（`related`）：CompareStoreToRegister 产生比较掩码并写入 CMPMASK，SetCmpMask 则从内存显式装载 CMPMASK；二者是 Select 前置掩码的两条来源路径。
- [Compares](compares.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《SetCmpMask》具体提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [Select](select.md)（`related`）：不显式传 mask 的 Select 重载依赖 SetCmpMask 按 selMode 装载比较寄存器，模式0/1/2 的入参含义直接决定选择语义。
- [Select](../../reg_vector_compute/compare_and_select/select.md)（`related`）：SetCmpMask说明设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
- [Select](../../reg_vector_compute/mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《SetCmpMask》具体提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`related`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《SetCmpMask》提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
- [GetCmpMask](get_cmp_mask_isasi.md)（`same_topic`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《SetCmpMask》明确提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
<!-- cannbot:related:end -->
