---
type: API
title: GetCmpMask
description: 获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GetCmpMask_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GetCmpMask

获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。

逐元素比较两个tensor大小，如果比较后的结果为真，则输出结果的对应比特位为1，否则为0。计算结果存入CmpMask 128bit寄存器中，可用于后续Select计算，也可使用GetCmpMask接口获取寄存器保存的数据。 接口支持多种比较模式： - LT：小于（less than） - GT：大于（greater than） - GE：大于或等于（greater than or equal to） - EQ：等于（equal to） - NE：不等于（not equal to） - LE：小于或等于（less than or equal to）

本接口组包含 Compare（结果存入寄存器）, Compare（结果存入寄存器）, Compare（结果存入寄存器）, LocalTensor, Compare（结果存入寄存器）。

本接口属于 UB 矢量计算比较与选择接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；本接口没有repeat输入，repeat默认为1，即一条指令计算256B的数据。；本接口将结果写入128bit的CmpMask寄存器中，可以用GetCmpMask接口获取寄存器保存的数据。；对UB空间的占用说明。针对Ascend 950PR/Ascend 950DT，该接口占用8KB Unified Buffer临时空间。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品 AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select CMPMASK_SPR 模式致混合分支误选》明确提供“arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》明确提供“arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select cmpmask 不偏移致分支反转诊断》明确提供“arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《arch35 Select cmpmask SPR 跨调用泄漏致非确定失败》明确提供“arch35 Select(VSEL_CMPMASK_SPR) cmpmask SPR 跨调用残留致分支错乱；case 单独 PASS、套件内 FAIL 为判别信号。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [arch35 Select 超64 cmpmask 残缺判别](../../../../../runbooks/precision/arch35_select_64_cmpmask.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《arch35 Select 超64 cmpmask 残缺判别》明确提供“arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染》明确提供“arch35 上 Compare + Select(VSEL_CMPMASK_SPR) 在标量/小 count 批跑时出现 Actual=Golden/2，单跑 PASS；切换 VSEL_TENSOR_TENSOR_MODE 仅将失败从 121 降至 52。MaskUnPack 读取 stale padding 是待独立验证的解释，不是已确认机制。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [AscSelect](../../../c_api/reg/compare_and_select/asc_select.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《GetCmpMask》补充：获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
- [AscSetCmpMask](../../../c_api/vector_compute/asc_set_cmp_mask.md)（`related`）：GetCmpMask说明获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果；对AscSetCmpMask而言，AscSetCmpMask 的输出由 AscSelect 消费，Compare/GetCmpMask 是掩码来源与观测点；完整套件失败而单例通过可诊断 SPR 泄漏。
- [Compare](compare.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Compare》明确提供“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [CompareStoreToRegister](compare_store_to_register.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《CompareStoreToRegister》明确提供“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Compares](compares.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Compares》明确提供“逐元素比较一个tensor中的元素和另一个标量的大小，结果为真的对应比特位为1，否则为0。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](select.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select》明确提供“根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../reg_vector_compute/compare_and_select/select.md)（`related`）：GetCmpMask说明获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
- [Select](../../reg_vector_compute/mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《GetCmpMask》具体提供“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SelectFlexibleScalar](select_flexible_scalar.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《SelectFlexibleScalar》明确提供“提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [AscGetCmpMask](../../../c_api/vector_compute/asc_get_cmp_mask.md)（`same_topic`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《AscGetCmpMask》明确提供“此接口用于获取Compare操作的比较结果。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [SetCmpMask](set_cmp_mask_isasi.md)（`same_topic`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《SetCmpMask》明确提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
<!-- cannbot:related:end -->
