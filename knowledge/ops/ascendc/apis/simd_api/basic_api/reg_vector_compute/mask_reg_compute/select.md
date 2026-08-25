---
type: API
title: Select
description: 根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.vector]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/MaskReg_compute/Select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---
# Select

头文件路径为："basic_api/reg_compute/kernel_reg_compute_maskreg_intf.h"。

给定两个源操作数src0和src1，根据mask的比特位值选取元素，得到目的操作数dst。选择的规则为：当mask的比特位是1时，从src0中选取对应位置的数，比特位是0时从src1选取对应位置的数。

参数：dst: 目的操作数，类型为MaskReg。；src0: 源操作数，类型为MaskReg。；src1: 源操作数，类型为MaskReg。；mask: 指示选择src0或src1，类型为MaskReg。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [B16 比较先升到 B32 锁定索引 lane](../../../../../runbooks/precision/b16_value_and_b32_index_masks_need_common_b32_compute.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《B16 比较先升到 B32 锁定索引 lane》具体提供“cummin/argmin 前缀扫描同时更新 B16 值与 int32 索引时，128-lane 比较 mask 不能驱动 64-lane 索引 Select；先升 float 统一 B32 lane。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select CMPMASK_SPR 模式致混合分支误选》具体提供“arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》具体提供“arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select cmpmask 不偏移致分支反转诊断》具体提供“arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select dst==src 别名破坏张量输入值》具体提供“AscendC Select 在 dst 与 src0 或 src1 同一 LocalTensor 时先写 dst 破坏 src 原值，导致按 mask 应保留的源值被改成中间临时值；通过在 Select 后插入 DataCopy 探针或检查 dst==src 别名定位。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](../../../../../runbooks/precision/arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》具体提供“arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select cmpmask SPR 跨调用泄漏致非确定失败》具体提供“arch35 Select(VSEL_CMPMASK_SPR) cmpmask SPR 跨调用残留致分支错乱；case 单独 PASS、套件内 FAIL 为判别信号。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select 异步SIMT同步失效致分支错选》具体提供“arch35 (DAV_3510, Ascend950) 上 Select 的 VSEL_CMPMASK_SPR 模式内部 set_cmpmask 为异步 SIMT，而 arch35 无 asc_sync_vec 实现、PipeBarrier<PIPE_V> 无法保证 vsel 前 CMPMASK 就绪，导致分支选择非确定地取到上一轮 stale CMPMASK 值。诊断方法与可用/失效同步手段的实测结论。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 Select 超64 cmpmask 残缺判别](../../../../../runbooks/precision/arch35_select_64_cmpmask.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 Select 超64 cmpmask 残缺判别》具体提供“arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染》具体提供“arch35 上 Compare + Select(VSEL_CMPMASK_SPR) 在标量/小 count 批跑时出现 Actual=Golden/2，单跑 PASS；切换 VSEL_TENSOR_TENSOR_MODE 仅将失败从 121 降至 52。MaskUnPack 读取 stale padding 是待独立验证的解释，不是已确认机制。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 count Compare Select 异步VF 存读 RAW》具体提供“Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../../../../../runbooks/compilation/arch35_select_32b_507035.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035》具体提供“为绕过 VselImpl 不偏移 sel 指针的问题，尝试分块 Select(SEL_CHUNK=64) 用 bMask[off>>3] 按 bitmask 偏移 mask 张量；第二块起 mask 源地址落 byte 8 非 32B 对齐，set_cmpmask 加载致 AIC runtime error 507035 崩溃。n=64 单块通过、n>=128 多块崩溃。banned 路线——对齐与 cmpmask 宽度约束互斥，无分块粒度可同时满足。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane](../../../../../runbooks/precision/compute_lane_count_must_follow_promoted_fp32_width.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《b16 提升 fp32 比较后按存储宽度分块会漏掉后半 lane》具体提供“2-byte 数据提升为 fp32 比较时，分块宽度必须按比较类型的单 repeat lane 数计算，否则后半 lane 不更新。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [半精度索引错位—拆分双 int32 掩码](../../../../../runbooks/precision/b16_value_mask_must_split_for_two_int32_index_registers.md)（`exemplifies`）：本卡用低、高 MaskReg 分别更新两个 int32 RegTensor；Reg Select 是索引锁步更新的执行点。
- [累计极值 NaN 语义须用 self-NE 合成选择掩码](../../../../../runbooks/precision/ordered_compare_alone_cannot_propagate_nan_prefix_state.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《累计极值 NaN 语义须用 self-NE 合成选择掩码》具体提供“累计极值 Vector scan 在有限值全部正确、全 NaN 输入却同时出现 NaN 位置和索引失配时，用显式 is-current-NaN、is-running-NaN 与有限 LE 合成选择掩码。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [AscSetCmpMask](../../../c_api/vector_compute/asc_set_cmp_mask.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《AscSetCmpMask》具体提供“为asc_select操作设置作用于选择的Mask掩码。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [GetCmpMask](../../memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《GetCmpMask》具体提供“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [MaskGenWithRegTensor](../reg_data_load/mask_gen_with_reg_tensor_mask_reg.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《MaskGenWithRegTensor》具体提供“将数据从RegTensor搬运至MaskReg，通过offset参数选择数据块，b16类型每个bit广播为2bit，b32类型每个bit广播为4bit。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [MaskReg](../register_data_types/mask_reg.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《MaskReg》具体提供“MaskReg寄存器用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之一。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [Select](../compare_and_select/select.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select》具体提供“根据mask比特位值从两个源操作数中选取元素，比特位为1选srcReg0，为0选srcReg1。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetCmpMask](../../memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`related`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《SetCmpMask》具体提供“设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
<!-- cannbot:related:end -->
