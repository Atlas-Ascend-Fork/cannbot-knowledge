---
type: API
title: Select
description: 根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# Select

头文件路径为："basic_api/reg_compute/kernel_reg_compute_vec_cmpsel_intf.h"。

给定两个源操作数srcReg0和srcReg1，根据mask的比特位值选取元素，得到目的操作数dstReg。当mask的比特位是1时，从srcReg0中选取对应位置的数，比特位是0时从srcReg1选取对应位置的数。

参数：T: 操作数数据类型。；U: 源操作数和目的操作数的RegTensor类型，例如RegTensor，由编译器自动推导，用户不需要填写。；dstReg(输出): 目的操作数。 类型为RegTensor。；srcReg0、srcReg1(输入): 源操作数。 类型为RegTensor。 两个源操作数的数据类型需要与目的操作数保持一致。；mask(输入): 指定选择源操作数的规则：mask的比特位是1时，选取srcReg0，比特位是0时，选取srcReg1。

支持数据类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16_t、int32_t、uint32_t、float、int64_t、uint64_t。

约束：通过mask参数控制的未选中的元素保持源操作数的值而非清零。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [GE图模式263: 自定义VF Select被禁](../../../../../runbooks/compilation/ge_263_vf_select.md)（`exemplifies`）：GE图模式263: 自定义VF Select被禁说明MaskedFill kernel 用 __simd_vf__/asc_vf_call 自定义 VF 实现 Select，aclnn 预编译全绿但 GE 图模式 TBE 动态编译生成坏 binary 触发 AI Core error 263（aivec）；须跑图模式的 regbase kernel 中自定义 VF 路线 banned。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：Select VSEL_CMPMASK_SPR count>64 掩码错位判别说明arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：Select cmpmask 不偏移致分支反转诊断说明arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：Select dst==src 别名破坏张量输入值说明AscendC Select 在 dst 与 src0 或 src1 同一 LocalTensor 时先写 dst 破坏 src 原值，导致按 mask 应保留的源值被改成中间临时值；通过在 Select 后插入 DataCopy 探针或检查 dst==src 别名定位。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败说明arch35 Select(VSEL_CMPMASK_SPR) cmpmask SPR 跨调用残留致分支错乱；case 单独 PASS、套件内 FAIL 为判别信号。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选说明arch35 (DAV_3510, Ascend950) 上 Select 的 VSEL_CMPMASK_SPR 模式内部 set_cmpmask 为异步 SIMT，而 arch35 无 asc_sync_vec 实现、PipeBarrier<PIPE_V> 无法保证 vsel 前 CMPMASK 就绪，导致分支选择非确定地取到上一轮 stale CMPMASK 值。诊断方法与可用/失效同步手段的实测结论。
- [arch35 Select 超64 cmpmask 残缺判别](../../../../../runbooks/precision/arch35_select_64_cmpmask.md)（`exemplifies`）：arch35 Select 超64 cmpmask 残缺判别说明arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW说明Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。
- [Compare](compare.md)（`related`）：Compare 产生的 MaskReg 可直接驱动 Reg Select，组成比较后选择链。
- [Compares](compares.md)（`related`）：“Compares”定义：逐元素比较RegTensor中每个元素与标量的大小关系，结果为真则MaskReg对应比特位置1。；“Select”定义：根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。。实质衔接：Reg Compares 生成 MaskReg；Compare 区分 tensor-tensor，Select 消费该 mask，AscLtScalar 展示 C API 的具体标量谓词映射。
- [GetCmpMask](../../memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`related`）：GetCmpMask说明获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
- [Select](../../../adv_api/data_filter/select.md)（`related`）：Reg Select 将条件选择留在寄存器链中，补充高阶 Tensor Select 之外避免中间 UB 往返的实现路线。
- [Select](../mask_reg_compute/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select》具体提供“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetCmpMask](../../memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`related`）：SetCmpMask说明设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
- [AscGeScalar](../../../c_api/reg/compare_and_select/asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；Select正文界定“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [AscLe](../../../c_api/reg/compare_and_select/asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；Select正文说明“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [AscSelect](../../../c_api/reg/compare_and_select/asc_select.md)（`same_topic`）：AscSelect说明根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。
- [Select](../../memory_vector_compute/compare_and_select/select.md)（`same_topic`）：Select说明根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
- [SelectFlexibleScalar](../../memory_vector_compute/compare_and_select/select_flexible_scalar.md)（`same_topic`）：SelectFlexibleScalar说明提供灵活标量位置的Select接口，支持标量在前和标量在后两种场景，标量可配置为LocalTensor单点元素。
<!-- cannbot:related:end -->
