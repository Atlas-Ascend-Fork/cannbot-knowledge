---
type: API
title: Select
description: 根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Select

根据 mask 从两个源 tensor 中选择元素，mask 为 1 选 src0，为 0 选 src1。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 全量清零 padding 覆盖有效区 banned](../../../../../runbooks/precision/duplicate_padding_banned.md)（`exemplifies`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：Select 接口给出三种选择模式和 mask 分支语义，本卡用 mode 0 与 tensor mode 的单变量 A/B 验证多 repeat 行为差异。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select”定义：根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：故障调用就是 AscendC::Select 的 VSEL_CMPMASK_SPR 模式；文档给出 sel、分支输入、模式、count 契约。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：官方 API 定义 mask=1 取 src0、mask=0 取 src1，给 focal 的 DataCopy 探针提供期望值基线；若 mask=0 而 dst 未保留 src1，才能继续判别别名破坏。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：该 runbook 处理另一类 Select 故障：VSEL_CMPMASK_SPR 内部异步 set_cmpmask 未完成导致 stale mask，能与 count>64 复用和 dst 别名问题区分。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《Select》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《Select》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../../../../../runbooks/compilation/arch35_select_32b_507035.md)（`exemplifies`）：错误在 SetCmpMask→Select 的消费链上显现；Select 输出或异常是验证掩码地址修正的直接观察点。
- [AscLt](../../../c_api/reg/compare_and_select/asc_lt.md)（`related`）：Select说明根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
- [AscSelect](../../../c_api/reg/compare_and_select/asc_select.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select》补充：根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
- [Compare](compare.md)（`related`）：Compare 产生逐元素真假掩码，Select 按同一掩码在 src0/src1 间取值，二者构成条件选择的直接生产者—消费者链。
- [CompareStoreToRegister](compare_store_to_register.md)（`related`）：《Select》明确“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”；它与《CompareStoreToRegister》的“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”在实际调用参数、数据流或结果校验上直接衔接。
- [Compares](compares.md)（`related`）：《Compares》的任务是“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”。《Select》具体提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，它直接用于Compares 生成标量比较 mask 并由 Select/SetCmpMask/GetCmpMask 消费的链路。
- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select》明确提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../../adv_api/data_filter/select.md)（`related`）：基础 Select 提供更底层的 UB 选择路径，并具有不同的 mask 模式和尾块约束，适合在高阶接口之外做实现选型。
- [SetCmpMask](set_cmp_mask_isasi.md)（`related`）：不显式传 mask 的 Select 重载依赖 SetCmpMask 按 selMode 装载比较寄存器，模式0/1/2 的入参含义直接决定选择语义。
- [Select](../../reg_vector_compute/compare_and_select/select.md)（`same_topic`）：Select说明根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`same_topic`）：《SelectFlexibleScalar》处理“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”。《Select》提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，其具体合同或探针直接接入灵活标量 Select 的标量来源、Compare mask 生产和别名安全。
<!-- cannbot:related:end -->
