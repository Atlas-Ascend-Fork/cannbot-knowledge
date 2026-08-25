---
type: API
title: Compare
description: 逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.compute.elementwise.comparison_logic]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/Compare.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Compare

逐元素比较两个 tensor 大小，结果为真则对应比特位为 1，否则为 0。支持 EQ、NE、GT、GE、LT、LE 等比较模式。头文件 `basic_api/kernel_operator_vec_cmpsel_intf.h`。dst 按小端排序为二进制结果。支持 950/a2/a3。

<!-- cannbot:related:start -->
## 相关

- [Duplicate 全量清零 padding 覆盖有效区 banned](../../../../../runbooks/precision/duplicate_padding_banned.md)（`exemplifies`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《Compare》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [Select cmpmask 不偏移致分支反转诊断](../../../../../runbooks/precision/select_cmpmask.md)（`exemplifies`）：本卡用 Compare 生成 bMask 并逐 bit 证明正确；文档给出谓词和 mask 布局契约。
- [arch35 Select 异步SIMT同步失效致分支错选](../../../../../runbooks/precision/arch35_select_simt.md)（`exemplifies`）：arch35 Select 异步SIMT同步失效致分支错选 与《Compare》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../../../../../runbooks/precision/arch35_vsel_cmpmask_spr_mask.md)（`exemplifies`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《Compare》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 count Compare Select 异步VF 存读 RAW](../../../../../runbooks/precision/arch35_count_compare_select_vf_raw.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《Compare》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [AscGtScalar](../../../c_api/reg/compare_and_select/asc_gt_scalar.md)（`related`）：Compare说明逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式；对AscGtScalar而言，AscGtScalar 的标量右操作数语义需与 AscGt 的双 Tensor、AscLtScalar 的反向比较以及 Compare 的通用模式区分。
- [AscLt](../../../c_api/reg/compare_and_select/asc_lt.md)（`related`）：Compare说明逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
- [AscNeScalar](../../../c_api/reg/compare_and_select/asc_ne_scalar.md)（`related`）：Compare说明逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。
- [Compare](../../reg_vector_compute/compare_and_select/compare.md)（`related`）：Memory Compare 在 LocalTensor 上执行同一谓词族，可按数据位置在 Memory 与 Reg 路线间选型。
- [GatherMask](gather_mask.md)（`related`）：《Compare》明确“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”；它与《GatherMask》的“以内置固定模式或用户自定义Tensor为gather mask，从源操作数中选取元素写入目的操作数。”在实际调用参数、数据流或结果校验上直接衔接。
- [GetCmpMask](get_cmp_mask_isasi.md)（`related`）：《GetCmpMask》处理“获取CompareStoreToRegister指令写入CmpMask寄存器的比较结果。”。《Compare》明确提供“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”，其参数、调用或验证步骤直接接入GetCmpMask 对 CompareStoreToRegister 产出 mask 的读取和 Select 消费链。
- [Select](select.md)（`related`）：Compare 产生逐元素真假掩码，Select 按同一掩码在 src0/src1 间取值，二者构成条件选择的直接生产者—消费者链。
- [CompareStoreToRegister](compare_store_to_register.md)（`same_topic`）：《Compare》明确“逐元素比较两个tensor大小，结果为真的对应比特位为1，否则为0，支持LT、GT、GE、EQ、NE、LE六种比较模式。”；它与《CompareStoreToRegister》的“逐元素比较两个tensor大小，结果存入CmpMask 128bit寄存器，可用于后续Select计算。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->
