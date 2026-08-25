---
type: API
title: 比较与选择
description: 寄存器矢量比较与选择接口集合，涵盖Compare、Compares、Select和Squeeze等操作。
tags: [task.lookup, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---

# 比较与选择

Reg 矢量比较与选择接口集合。Compare/Compares 执行逐元素比较；Select 按条件从两个 Tensor 中选取元素；Squeeze 用于压缩指定维度。相比 Memory 版本接口更精简，结果直接保存在寄存器中，适合需要低延迟比较的场景。

<!-- cannbot:related:start -->
## 相关

- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：Select VSEL_CMPMASK_SPR count>64 掩码错位判别说明arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：Select cmpmask 不偏移致分支反转诊断说明arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [Select dst==src 别名破坏张量输入值](../../../../../runbooks/precision/select_dst_src.md)（`exemplifies`）：Select dst==src 别名破坏张量输入值说明AscendC Select 在 dst 与 src0 或 src1 同一 LocalTensor 时先写 dst 破坏 src 原值，导致按 mask 应保留的源值被改成中间临时值；通过在 Select 后插入 DataCopy 探针或检查 dst==src 别名定位。
- [arch35 Select 超64 cmpmask 残缺判别](../../../../../runbooks/precision/arch35_select_64_cmpmask.md)（`exemplifies`）：arch35 Select 超64 cmpmask 残缺判别说明arch35（DAV_3510）上 Compare 一次产生的 cmpmask 有效位限 256B/sizeof(T)=64（fp32）；kernel 把 count_padded（可达 1088+）一次性传给 Compare/Select(VSEL_CMPMASK_SPR) 时，超出 64 的 cmpmask 残缺/陈旧，Select 据残缺掩码对第 65+ 元素取错分支。判别=固定 threshold≈0、放大 count_padded 做边界实验，PASS/FAIL 边界恰在 64 即定位。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW说明Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。
- [AscEqScalar](../../../c_api/reg/compare_and_select/asc_eq_scalar.md)（`related`）：CompareAndSelect 总览定位 Reg 比较、掩码和选择流水，说明 AscEqScalar 的输出如何进入后续 Select。
- [AscGe](../../../c_api/reg/compare_and_select/asc_ge.md)（`related`）：Reg 比较与选择入口把 AscGe 所属的比较结果生成和后续 Select/Squeeze 消费放在同一工作流中。
<!-- cannbot:related:end -->
