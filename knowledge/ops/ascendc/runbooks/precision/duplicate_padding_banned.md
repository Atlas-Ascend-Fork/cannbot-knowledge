---
type: "Runbook"
title: "Duplicate 全量清零 padding 覆盖有效区 banned"
description: "模式2 Select 在 count 非 64 整数倍时 padding 区垃圾 mask 污染有效元素；用 Duplicate(buf,0,count_padded) 全量清零 padding 会因 Duplicate 无 offset 语义覆盖有效 gradOutput 致回归——banned，须源头清零或区间清零。"
tags: ["task.debugging", "topic.precision", "topic.implementation.masking"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["softplus_v2_grad"]
---

# Duplicate 全量清零 padding 覆盖有效区 banned

## 现象

SoftplusV2Grad arch35 kernel 在修复 Select 模式0→模式2（见姊妹卡 `arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64`）后，仍残留 8 例 `Actual≈Golden/2`，全部 `mismatch=1/1`（单元素用例），ratio 恒为 0.5。场景是 `count=1` 但 `count_padded=64`（Select/Compare 按 256B=64 float 对齐）：模式2 每 64 元素连续消耗 selMask 的不同部分，但 `Compare` 只对 `count_padded=64` bit 写了 mask，其中后 63 bit 对应 padding 区域是未初始化垃圾值；padding 的垃圾 mask 经模式2 连续消耗污染了第 0 个有效元素的选择，使其错走 sigmoid（输出 g×0.5）。

为消除 padding 垃圾，尝试用 `Duplicate(buf, 0, count_padded)` 把 padding 区域填 0，但该全量清零路线客观回归，banned。

## 适用场景

- **工程形态**：ops-registry-invoke 算子仓开发，arch35 kernel 直调，用 `Compare`+`Select` 模式2 做 cmpmask 二选一分支，且 `count` 不是 64 的整数倍。
- **API 路径**：`AscendC::Compare`(cmpmask) + `AscendC::Select`(VSEL_TENSOR_TENSOR_MODE) + `AscendC::Duplicate`。
- **验证平台与版本**：Ascend950PR（3510/DAV_3510，平台 token `950`），CANN cann-9.0.0-beta.2。
- **适用粒度**：operator_family（任何 arch35/950 kernel 用模式2 Select 且 count 非 64 整数倍）。
- **路线优先级**：banned（全量 `Duplicate(buf, 0, count_padded)` 清 padding 这条路线在本 trace 客观回归，banned）。
- **不适用或未验证场景**：count 恒为 64 整数倍的 kernel 无 padding 区域，不触发；模式0（VSEL_CMPMASK_SPR）的 padding 行为不同，不在本卡范围。

## 失败路线

**尝试**：在 `Select` 之前对 `bBx`（输入）与 `bG`（gradOutput）各调用 `Duplicate(buf, 0.0f, count_padded)`，期望把 padding 区域（`[count, count_padded)`）填 0，使 bx=0 ≤ threshold → mask=false → sigmoid → padding 输出 0，从而消除垃圾 mask 对有效元素的污染。

**失败 / 回退**：

1. `Duplicate(bBx, 0, count_padded)` 把 `bBx` 从 0 开始全量填 0，连第 0 个有效元素也被清成 0。
2. `Duplicate(bG, 0, count_padded)` 同样从 0 开始全量填 0，覆盖了 `bG`（gradOutput）的有效元素——`Duplicate` 不支持 offset 操作，只能从 0 开始填整个 `count_padded`，无法只清 `[count, count_padded)` 区间。
3. 重建跑 C++ ST 真机（`tests/st/run.sh --real`）：通过数由 57 跌到 15（回归），证明全量清零覆盖有效 gradOutput 后输出失真。
4. 回退该修改：C++ ST 恢复 57/57、PyTorch ST 恢复 523/581。

**banned**：`Duplicate(buf, 0, count_padded)` 全量清零 padding 区域——`Duplicate` 无 offset 语义，连有效元素一起覆盖，引入回归。padding 区域的确定性须改走源头清零（CopyIn 阶段填 0）或带 offset/stride 的区间清零，不能用单条全量 `Duplicate`。

## 验证信号

- 全量清零 padding 后 C++ ST 真机通过数下降（回归）（来源平台：950；证据等级: tool_observed）
- 回退后 C++ ST 与 PyTorch ST 通过数恢复（来源平台：950；证据等级: tool_observed）
- Select 模式2 修复后仍残留 8 例单元素 1/1 mismatch（Actual≈Golden/2），根因指向 padding 垃圾 mask 污染（来源平台：950；证据等级: tool_observed）

## 预防

- padding 区域的确定性是模式2 Select 的前提：使用模式2 前应保证 padding 区域的输入（bx、bG）与 mask 都是确定值，但不能用全量 `Duplicate`（会覆盖有效区）。
- 正确方向（本 trace 未落定干净修复，仅指明接续点）：① 在 `CopyIn` 阶段就把 padding 区域填 0（源头保证，而非事后清零）；② 或用带 offset 的 API（如 `Copy` 带 stride）只清 `[count, count_padded)` 区间；③ 或保证 padding 区域的 bx 取一个确定性安全值（如 threshold+1 使 mask 确定走线性）。
- 单元素用例（count=1）必须进 C++ ST，否则 padding 污染不在 L0 暴露。

## 失效边界

- 950PR（3510）已实测；`Duplicate` 无 offset 语义是 API 契约，950DT（同 DAV_3510）同样成立，未单独验证。
- 2201（Ascend910B）的模式2 selMask 连续消耗行为可能不同，未在本 trace 验证。
- 推断可迁移平台（950DT、2201）均标注"未验证，推断可迁移"。

## 误诊

agent 初判"padding 垃圾 mask 污染有效元素"方向正确，但修复方案（全量 `Duplicate` 清零）未考虑 `Duplicate` 无 offset 语义会覆盖有效区，导致回归。正确接续点应是源头清零或区间清零。

<!-- cannbot:related:start -->
## 相关

- [Compare](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/compare.md)（`exemplifies`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Compare》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Duplicate](../../apis/simd_api/basic_api/memory_vector_compute/data_padding/duplicate.md)（`exemplifies`）：“Duplicate”定义：将变量或立即数复制多次并填充到向量中，支持前n个数据计算和高维切分计算两种方式。；“Duplicate 全量清零 padding 覆盖有效区 banned”定义：模式2 Select 在 count 非 64 整数倍时 padding 区垃圾 mask 污染有效元素；用 Duplicate(buf,0,count_padded) 全量清零 padding 会因 Duplicate 无 offset 语义覆盖有效 gradOutput 致回归——banned，须源头清零或区间清零。。实质衔接：这些卡分别限定 Duplicate 的等价 Reg/C API、UB 清零和标量广播正用法，以及全量 padding 覆盖、归约标量来源和纯写预填充的失败/性能边界。
- [Select](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/select.md)（`exemplifies`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [InitOutput GM 专用，UB 清零用 Duplicate](../compilation/initoutput_gm_ub_duplicate.md)（`related`）：InitOutput GM 专用，UB 清零用 Duplicate 与《Duplicate 全量清零 padding 覆盖有效区 banned》的实质衔接是：InitOutput 只接受 GM GlobalTensor，而 UB LocalTensor 要用 Duplicate；相关 API、类型错误、TBuf 取 LocalTensor 和清零覆盖故障直接验证该边界。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`related`）：为清理 CMPMASK padding 而全量 Duplicate 会覆盖有效 gradOutput；目标卡否定这一绕过路线，补充本卡 MODE A/B 之外的修复边界。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select VSEL_CMPMASK_SPR count>64 掩码错位判别》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select cmpmask 不偏移致分支反转诊断》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select cmpmask SPR 跨调用泄漏致非确定失败》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select 异步SIMT同步失效致分支错选》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 Select 超64 cmpmask 残缺判别》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《Duplicate 全量清零 padding 覆盖有效区 banned》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 count Compare Select 异步VF 存读 RAW》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../compilation/arch35_select_32b_507035.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
<!-- cannbot:related:end -->
