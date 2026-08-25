---
type: API
title: AscSelect
description: 根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/reg/compare_and_select/asc_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# AscSelect

根据mask从源操作数src0、src1中选择元素，得到目的操作数dst。选择的规则为：当mask的比特位为1时，从src0中选取对应位置的数；当mask的比特位为0时，从src1中选取对应位置的数。

参数：`dst`(输出): 目的操作数（掩码寄存器或矢量数据寄存器）。；`src0`(输入): 源操作数0（掩码寄存器或矢量数据寄存器）。；`src1`(输入): 源操作数1（掩码寄存器或矢量数据寄存器）。；`mask`(输入): 源操作数掩码（掩码寄存器）。指定选择src0或src1为有效数据。mask的比特位为1时，选取src0；mask的比特位为0时，选取src1。

支持数据类型：half。

约束：- 通过mask参数控制的未选中的元素保持源操作数的值而非清零。
- src0、src1和dst的数据类型需要保持一致。

仅 Ascend 950PR/Ascend 950DT 支持。

<!-- cannbot:related:start -->
## 相关

- [Select CMPMASK_SPR 模式致混合分支误选](../../../../../runbooks/precision/select_cmpmask_spr.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select CMPMASK_SPR 模式致混合分支误选》补充：arch35(dav_c310) 高层 Select 用 VSEL_CMPMASK_SPR 时 set_cmpmask 不随 repeat 偏移 mask 指针，count 超过一个 repeat 的 64 个 fp32 元素时每 repeat 复用首 64bit mask 致混合分支误选；改 VSEL_TENSOR_TENSOR_MODE 后失败数由 116 降至 3 判明根因。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》补充：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select cmpmask 不偏移致分支反转诊断》补充：arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select dst==src 别名破坏张量输入值》补充：AscendC Select 在 dst 与 src0 或 src1 同一 LocalTensor 时先写 dst 破坏 src 原值，导致按 mask 应保留的源值被改成中间临时值；通过在 Select 后插入 DataCopy 探针或检查 dst==src 别名定位。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](../../../../../runbooks/precision/arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》补充：arch35 Select 模式0 VSEL_CMPMASK_SPR 的 selMask 有效位限 256/sizeof(T)=64，多轮迭代复用同一 64bit 掩码，count>64 时元素 p 实际取 bit(p%64)，导致跨 64 元素块掩码错配，sigmoid 区元素被误判为线性分支返回 gradOutput。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](../../../../../runbooks/precision/arch35_select_cmpmask_spr.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select cmpmask SPR 跨调用泄漏致非确定失败》补充：arch35 Select(VSEL_CMPMASK_SPR) cmpmask SPR 跨调用残留致分支错乱；case 单独 PASS、套件内 FAIL 为判别信号。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select 异步SIMT同步失效致分支错选》补充：arch35 (DAV_3510, Ascend950) 上 Select 的 VSEL_CMPMASK_SPR 模式内部 set_cmpmask 为异步 SIMT，而 arch35 无 asc_sync_vec 实现、PipeBarrier<PIPE_V> 无法保证 vsel 前 CMPMASK 就绪，导致分支选择非确定地取到上一轮 stale CMPMASK 值。诊断方法与可用/失效同步手段的实测结论。
- [arch35 Select 超64 cmpmask 残缺判别](../../../../../runbooks/precision/arch35_select_64_cmpmask.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 Select 超64 cmpmask 残缺判别》补充：arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padd
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染》补充：arch35 上 Compare + Select(VSEL_CMPMASK_SPR) 在标量/小 count 批跑时出现 Actual=Golden/2，单跑 PASS；切换 VSEL_TENSOR_TENSOR_MODE 仅将失败从 121 降至 52。MaskUnPack 读取 stale padding 是待独立验证的解释，不是已确认机制。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 count Compare Select 异步VF 存读 RAW》补充：Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../../../../../runbooks/compilation/arch35_select_32b_507035.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035》补充：为绕过 VselImpl 不偏移 sel 指针的问题，尝试分块 Select(SEL_CHUNK=64) 用 bMask[off>>3] 按 bitmask 偏移 mask 张量；第二块起 mask 源地址落 byte 8 非 32B 对齐，set_cmpmask 加载致 AIC runtime error 507035 崩溃。n=64 单块通过、n>=128 多块崩溃。banned 路线——对齐与 cmpmask 宽度约束互斥，无分块
- [AscEq](asc_eq.md)（`related`）：“AscEq”处理逐元素比较两个源操作数是否相等，比较结果写入目的操作数对应比特位，为真则置1，否则置0。仅在AIV上生效。；“AscSelect”明确根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。。实质衔接：AscEq 产生相等比较 mask；标量变体改变右操作数，AscNe 改变谓词，Reg Compare 是模板层等价能力，AscSelect 消费该 mask。
- [AscGe](asc_ge.md)（`related`）：AscSelect 消费 AscGe 等比较接口生成的 mask，在两个源寄存器之间逐 lane 选值。
- [AscSelect](../../vector_compute/asc_select.md)（`related`）：Reg AscSelect 实现同类条件选择但使用寄存器数据与 mask，可按 UB Vector 或 Reg 路线选型。
- [AscSetCmpMask](../../vector_compute/asc_set_cmp_mask.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《AscSetCmpMask》补充：为asc_select操作设置作用于选择的Mask掩码。
- [GetCmpMask](../../../basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《GetCmpMask》补充：获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。
- [Select](../../../basic_api/memory_vector_compute/compare_and_select/select.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select》补充：根据selMask比特位值从两个源操作数中选取元素，比特位为1选src0，为0选src1，支持三种选择模式。
- [SetCmpMask](../../../basic_api/memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`related`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《SetCmpMask》补充：设置CmpMask比较寄存器的值，配合不传入mask参数的Select接口使用。
- [AscGeScalar](asc_ge_scalar.md)（`same_topic`）：焦点处理AscGeScalar 的标量比较 mask 及 Select 消费路径；AscSelect正文界定“根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置”。候选生成相同 GE mask、提供标量 Compares，或由 Select/AscSelect 直接消费比较结果。
- [AscLe](asc_le.md)（`same_topic`）：焦点处理AscLe 的向量小于等于 mask 与标量/选择接口衔接；AscSelect正文说明“根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置”。候选生成同类比较 mask，或直接消费该 mask 完成 Select。
- [Select](../../../basic_api/reg_vector_compute/compare_and_select/select.md)（`same_topic`）：AscSelect说明根据mask从源操作数src0、src1中选择元素得到dst，mask比特位为1时选src0对应位置，为0时选src1对应位置。
<!-- cannbot:related:end -->
