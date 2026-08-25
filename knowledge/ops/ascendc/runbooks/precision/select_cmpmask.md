---
type: "Runbook"
title: "Select cmpmask 不偏移致分支反转诊断"
description: "arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。"
tags: ["task.debugging", "topic.compute.elementwise.comparison_logic", "topic.implementation.api_layer.basic_api", "topic.implementation.masking", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# Select cmpmask 不偏移致分支反转诊断

## 现象

在 Ascend950PR（arch35/dav_c100，CANN 9.0.0-beta.2）上调试 `softplus_v2_grad` 算子精度：L0 全部通过（51/51），但 L1 功能测试 115/578 失败。典型失败用例 L1_008（beta=-781.95，threshold=-0.0052，fp16，1204224 元素）约 1.2% element mismatch：对于 `z = beta*self > threshold` 的元素（应走线性分支返回 grad_output），kernel 返回了 sigmoid 分支值（约 0.5×grad_output）；反之 `z <= threshold` 的元素（应走 sigmoid）返回了 grad_output（线性）。失败率约 1.2%，数据相关（随机种子不同时失败位置变化）。fp32/fp16/bf16 均复现，排除 cast 问题。小规模通过、大规模失败，排除纯公式错误。

## 适用场景

- **工程形态**：kernel 直调（op_kernel/arch35 ComputeFp32Core 内部使用 `AscendC::Compare` + `AscendC::Select` 做二分支选择）。
- **API 路径**：`AscendC::Select<float, uint8_t>(dst, mask, src0, src1, SELMODE::VSEL_CMPMASK_SPR, count)`；底层 `kernel_operator_vec_cmpsel_impl.h` 的 `VselImpl`/`VselIntrinsicsImpl`/`set_cmpmask`。
- **验证过的平台与 CANN 版本**：Ascend950PR（arch35/dav_c100），CANN 9.0.0-beta.2；`platforms: [950]`。
- **适用粒度**：`operator_family`（任何在 arch35/dav_c100 上用 `Select(VSEL_CMPMASK_SPR)` 且 count 可能超过 128 fp32 元素的算子均受影响）。
- **不适用或未验证场景**：a2/a3 未验证；count ≤ 128 fp32 元素时原 Select 可正常工作；非 dav_c100 架构（如支持 VSEL_TENSOR_TENSOR_MODE 的其他 arch）未验证不受此问题影响。

## 判别方法

**触发（trigger，tool_observed）**：arch35/dav_c100 上以 `Select(VSEL_CMPMASK_SPR)` 做逐元素二分支选择的 kernel，L1 功能测试出现约 1.2% element mismatch 且失败位置呈周期性、数据相关；线性/sigmoid 分支返回值互换（mask 分支反转）。fp32/fp16/bf16 均复现，小规模通过、大规模失败。

**探针（probe，可执行检查）**：

1. **规模扫描**：固定一组失败用例的输入分布，按元素数 n 递增跑 L1 单算子用例（n=8/64/128/129/256…），记录 mismatch 数随 n 的变化。
2. **掩码—结果一致性比对**：在 `Compare` 写入的 bMask 张量与 `Select` 输出上各取同一元素下标，逐元素核对 mask bit 与实际选中分支是否一致（PRINTF dump bMask 逐 bit 与 `bx > threshold` 比对，再 dump Select 输出与 bMask 比对）。
3. **框架源码读取**：读 `kernel_operator_vec_cmpsel_impl.h` 的 `VselImpl`（约 line 216-268）与 `TSel.hpp` 的 `cmpmaskLen` 注释，确认 repeatRounding 循环中各指针的偏移情况与 cmpmask 加载宽度。

**观测（observation，tool_observed）**：

1. **规模阈值**：n=8/64/128 通过（0 mismatch），n=129 起 2 mismatches，n>128 持续失败——经验边界 128 fp32 元素。失败位置间距约 64（256B/4B=64 fp32 元素），指向 64 元素对齐边界。
2. **bMask 正确、Select 不一致**：`Compare` 写入的 bMask 张量逐 bit 与 `bx > threshold` 一致（正确）；但 `Select` 结果与 bMask 不一致——位于非首 64 元素块的元素，其 mask bit 与首块对应位置相反时，Select 返回了相反分支的值（mask 分支反转）。
3. **dav_c100 Select 仅支持 `VSEL_CMPMASK_SPR`**：其他模式 `ASCENDC_ASSERT false`，无法切换到从张量读 mask 的模式。
4. **VselImpl 在 repeatRounding 循环中不偏移 `sel` 指针**：每次 `VselIntrinsicsImpl(dst + dstOffset, sel, src0 + src0Offset, src1 + src1Offset, ...)` 中 `dst`/`src0`/`src1` 均按 `dstOffsetCount` 偏移，唯独 `sel` 始终传原始指针；`VselIntrinsicsImpl` 在 `VSEL_CMPMASK_SPR` 模式下调用 `set_cmpmask(sel)` 从该地址加载 cmpmask 寄存器再执行 `vsel`。

**判别（interpretation，根因归因）**：单一根因——`VselImpl` 的 repeatRounding 循环不偏移 `sel` 指针，导致当 count 超过单次 `set_cmpmask`+`vsel` 能正确覆盖的宽度时，后续 repeat 始终从 mask 张量首块加载 cmpmask，非首块元素的分支选择被首块 mask bit 覆盖，从而 mask 分支反转。这与“bMask 正确但 Select 结果不一致”“n 超阈值才失败”“失败间距约 64 元素”三项 tool_observed 观测自洽。判别要点：若 bMask dump 正确而 Select 输出在非首块位置发生分支互换、且 failure 随 n 跨过约 128 元素阈值出现，即可判定为本机制，而非公式错误、cast 问题或广播搬运问题（均已被观测排除）。

## 验证信号

判别所依据的实测信号（来源平台：950）：

- L0 51/51 通过、L1 115/578 失败，典型用例约 1.2% element mismatch（来源平台:950；证据等级:tool_observed）
- 规模扫描：n=8/64/128 通过（0 mismatch）、n=129 起 2 mismatches、n>128 持续失败，失败间距约 64 fp32 元素（来源平台:950；证据等级:tool_observed）
- 框架源码读取：dav_c100 Select 仅支持 `VSEL_CMPMASK_SPR`（其他模式 `ASCENDC_ASSERT false`）（来源平台:950；证据等级:tool_observed）
- 框架源码读取：`VselImpl` repeatRounding 循环中 `sel` 指针不随 repeat 偏移，`dst`/`src0`/`src1` 均按 `dstOffsetCount` 偏移（来源平台:950；证据等级:tool_observed）
- 判别后据此改用纯算术掩码折叠分支，L1 失败从 115/578 降至 58/578（57 个 mask 分支反转用例全部修复、0 回归）、C++ ST 57/57 通过，反证判别正确（来源平台:950；证据等级:tool_observed）

剩余 58 个失败均为极端值边界用例（±FLT_MAX/inf/nan/subnormal threshold），在原始 baseline 同样失败，为独立问题，非本机制。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《Select cmpmask 不偏移致分支反转诊断》补充：arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [Compare](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/compare.md)（`exemplifies`）：本卡用 Compare 生成 bMask 并逐 bit 证明正确；文档给出谓词和 mask 布局契约。
- [GetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/get_cmp_mask_isasi.md)（`exemplifies`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Select cmpmask 不偏移致分支反转诊断》明确提供“arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/select.md)（`exemplifies`）：故障调用就是 AscendC::Select 的 VSEL_CMPMASK_SPR 模式；文档给出 sel、分支输入、模式、count 契约。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/select.md)（`exemplifies`）：Select cmpmask 不偏移致分支反转诊断说明arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《Select cmpmask 不偏移致分支反转诊断》具体提供“arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetCmpMask](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/set_cmp_mask_isasi.md)（`exemplifies`）：VselIntrinsicsImpl 每 repeat 调 set_cmpmask(sel)，接口说明从地址装载 cmpmask。
- [比较与选择](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`exemplifies`）：Select cmpmask 不偏移致分支反转诊断说明arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。
- [SoftplusV2Grad 非默认θ线性区分支缺失致超差](softplusv2grad.md)（`related`）：候选处理 softplus_v2_grad 非默认 threshold 公式分支，本卡处理正确 mask 被 Select 错误消费。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`related`）：候选处理标量批跑中 SPR mask 污染，本卡处理张量多 repeat 首块复用。
- [arch35 count Compare Select 异步VF 存读 RAW](arch35_count_compare_select_vf_raw.md)（`related`）：候选处理 Compare 生产 mask 与 Select 消费间缺 VF RAW；本卡先证明 bMask 正确再定位地址复用。
- [arch35 分块 Select 掩码偏移非 32B 对齐崩溃 507035](../compilation/arch35_select_32b_507035.md)（`related`）：候选记录按64元素偏移 mask 绕过 sel 不偏移时，第二块8B地址不满足 set_cmpmask 32B 对齐而崩。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Select cmpmask 不偏移致分支反转诊断》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`same_topic`）：两卡均从 VselImpl 的 repeat 循环确认 sel 指针不偏移，导致 count 超过 64 个 fp32 元素后复用首块 CMPMASK 并反转混合分支。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`same_topic`）：“Select VSEL_CMPMASK_SPR count>64 掩码错位判别”定义：arch35 Select 的 VSEL_CMPMASK_SPR 对 float 仅载首 repeat 的 selMask 并对所有 repeat 复用；count>64 时后续块套用首 64 元素块掩码，错误位置 pos%64 集中在 44/55/56，双向错取 linear/sigmoid 分支。判别：逐元素比对 golden 与 actual 求 pos%64 分布，n=15360 单完整 tile 复现排除 tile 边界。；“Select cmpmask 不偏移致分支反转诊断”定义：arch35/dav_c100 上 Select(VSEL_CMPMASK_SPR) 在 count>128 时 L1 出现约 1.2% element mismatch 与 mask 分支反转；通过 n 规模扫描与 VselImpl 源码读取定位为 repeatRounding 循环中 sel 指针不偏移、后续 repeat 复用首块 cmpmask。。实质衔接：这些卡以 64 元素周期、VselImpl sel 不偏移和首块 mask 复用闭合同一根因；分块修复受 32B 对齐阻断，Select/SetCmpMask 文档给出消费契约。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`same_topic`）：候选直接描述 count>64 后复用首块 mask，本卡确认 VselImpl 只偏移 dst/src 而不偏移 sel。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`same_topic`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《Select cmpmask 不偏移致分支反转诊断》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：arch35 Select 异步SIMT同步失效致分支错选 与《Select cmpmask 不偏移致分支反转诊断》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`same_topic`）：候选用超过 64 个元素的边界定位掩码残缺，本卡观测 n=129 起失败且约 64 元素周期。
<!-- cannbot:related:end -->
