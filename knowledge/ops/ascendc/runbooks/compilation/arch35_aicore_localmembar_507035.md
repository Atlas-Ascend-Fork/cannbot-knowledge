---
type: "Runbook"
title: "arch35 __aicore__ 调 LocalMemBar 报 507035"
description: "Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。"
tags: ["task.debugging", "topic.implementation.synchronization", "topic.implementation.pipeline"]
status: stable
sources: []
created_at: "2026-08-18T07:10:44Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["AIV_error", "count_based_Compare"]
---

# arch35 __aicore__ 调 LocalMemBar 报 507035

## 现象

在 Ascend950PR (arch35/dav_c310, CANN 9.0.0-beta.2) 排查 `softplus_v2_grad` 的 count-based Compare→Select async-VF mask VEC_STORE→VEC_LOAD RAW 隐患时，找到 arch35 上针对 VEC_STORE→VEC_LOAD 的专用内存屏障 `AscendC::Reg::LocalMemBar<Reg::MemType::VEC_STORE, Reg::MemType::VEC_LOAD>`（softmax regbase `SoftmaxFlashNDImpl` 在用）。尝试在 `ComputeFp32Core`（`__aicore__ inline` 常规函数）内、`Compare` 之后直接调用：

```
Reg::LocalMemBar<Reg::MemType::VEC_STORE, Reg::MemType::VEC_LOAD>();
```

两次独立尝试（旧 4-buffer 代码、新 5-buffer 重排代码）均触发运行时错误 507035 (AIV error)，kernel 执行失败。

## 适用场景

- **工程形态**：kernel 直调（RegBase，`__aicore__` 常规函数内调 `AscendC::` Level2 API，未把算子段包进 `__simd_vf__`）。
- **API 路径**：`AscendC::Reg::LocalMemBar<src, dst>`（头 `reg_compute/kernel_reg_compute_membar_intf_impl.h`）；`Reg::MemType::VEC_STORE` / `VEC_LOAD` / `SCALAR_LOAD`（头 `reg_compute/` 内 enum）。
- **验证过的平台与 CANN 版本**：Ascend950PR (arch35/dav_c310)，CANN 9.0.0-beta.2。仅本平台实测，`platforms: [950]`。
- **适用粒度**：`operator_family`（适用于 arch35 上任何想在 `__aicore__` 常规函数里调 `Reg::LocalMemBar` 的算子）。
- **路线优先级**：`banned`——从 `__aicore__` 直接调 `Reg::LocalMemBar` 作为修复手段 banned；须把调用点包进 `__simd_vf__` 函数或在 `__simd_vf__` 融合体内使用。
- **不适用或未验证场景**：`__simd_vf__` 函数内调用同一 API（softmax regbase 路径）不在本卡否定范围；非 arch35 平台 (a2/a3) 未验证，`__simd_callee__` 调用约定可能不同。

## 失败路线

> 来源：本 trace 在 Ascend950PR + CANN 9.0.0-beta.2 上的两次重编重跑。

**banned 路线：在 `ComputeFp32Core`（`__aicore__ inline`）内 `Compare` 之后直接插入 `Reg::LocalMemBar<VEC_STORE, VEC_LOAD>()`，意图排空 count-based Compare 的 async-VF VEC_STORE 使后续 Select 的 VEC_LOAD 可见。**

- **尝试**：两版独立代码（旧 4-buffer 代码、新 5-buffer 重排代码）均在 `Compare` 后插入上述 `Reg::LocalMemBar` 调用，重编重跑。
- **客观失败**：运行时 507035 (AIV error)，两次独立代码版本均复现，kernel 执行失败（来源平台:950；证据等级:tool_observed）。
- **边界**：`Reg::LocalMemBar` 声明为 `__simd_callee__`，要求调用点处于 `__simd_vf__` (VF) 调用上下文；从常规 `__aicore__` 函数直接调用违反调用约定，AIV 报 507035。该约束来自 CANN 头 `reg_compute/kernel_reg_compute_membar_intf_impl.h` 与 softmax regbase `SoftmaxFlashNDImpl`（`__simd_vf__ inline` 函数）在其内调用同一 API 的对照（来源平台:950；证据等级:artifact_verified）。故从 `__aicore__` 常规函数直接调 `Reg::LocalMemBar` 作为 count-based Compare→Select 隐患的最小 sync 修复，**banned**。
- **对照**：repeat-based Compare (Level0) 内部带 `Reg::LocalMemBar<VEC_STORE, SCALAR_LOAD>`（读 cmpmask 进 `g_cmpMaskLow`），而 count-based Compare (Level2) 内部无 LocalMemBar——这正是 RAW 隐患成因（来源平台:950；证据等级:artifact_verified）。

唯一本 trace 实测可见的排空仍是 `LocalTensor::GetValue` 标量同步；正向方向是把整段算子（含 Compare/Select）包进 `__simd_vf__` Reg:: 融合体，在 VF 上下文内按需用 `Reg::LocalMemBar`，或令 mask 全程留 MaskReg 不做 UB 往返——均未在本 trace 完成（重写未完成即被回退）。

## 验证信号

本段只收本 trace 内 tool_observed 实测与从 CANN 头源码逐字核对的结构事实（artifact_verified）；agent 推断的机制假设不进此段。

- 从 `__aicore__` 常规函数调 `Reg::LocalMemBar<VEC_STORE,VEC_LOAD>` 触发 507035 (AIV error)，两次独立代码版本（旧 4-buffer、新 5-buffer 重排）重编重跑均复现（来源平台:950；证据等级:tool_observed）
- `Reg::LocalMemBar` 声明为 `__simd_callee__`，softmax regbase `SoftmaxFlashNDImpl`（`__simd_vf__ inline` 函数）在其内调用同一 `Reg::LocalMemBar<VEC_STORE, VEC_LOAD>`（头 `reg_compute/kernel_reg_compute_membar_intf_impl.h`、`.../softmax/regbase/c310/softmax_flash_impl.h`）（来源平台:950；证据等级:artifact_verified）
- count-based Compare (Level2) 内部无 `LocalMemBar`；repeat-based Compare (Level0) 内部带 `Reg::LocalMemBar<VEC_STORE, SCALAR_LOAD>`（头 `.../reg_compute/dav_c310/kernel_reg_compute_vec_cmpsel_impl.h`）（来源平台:950；证据等级:artifact_verified）

## 失效边界

- 本卡否定的是「从 `__aicore__` 常规函数直接调用」这一调用上下文；在 `__simd_vf__` 函数内调用同一 API 不受否定（softmax regbase 路径即如此）。
- 非 arch35 平台 (a2/a3) 未验证，`__simd_callee__` 调用约定可能不同；**未验证，推断可迁移**性低。
- 把整段算子包进 `__simd_vf__` 后 `Reg::LocalMemBar<VEC_STORE,VEC_LOAD>` 是否真能排空该 RAW 隐患，未在本 trace 验证（重写未完成即被回退），不作为本卡结论。

## 坏实践

- 在 `__aicore__` 常规 kernel 函数里直接调 `Reg::` (`__simd_callee__`) 命名空间的 sync API，不看调用上下文约束。
- 据 softmax regbase「能调 `Reg::LocalMemBar`」反推任意 kernel 都能直接调——softmax 是在 `__simd_vf__` 函数内调用，调用上下文不同。

<!-- cannbot:related:start -->
## 相关

- [Async](../../apis/simd_api/basic_api/tool_interface/execution_mode/async.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《Async》明确提供“通过模板函数封装AIC与AIV分离模式的硬件条件分支，在指定执行单元下执行特定函数，避免代码中显式使用硬件条件分支。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [LocalMemBar](../../apis/simd_api/basic_api/reg_vector_compute/sync_control/local_mem_bar.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《LocalMemBar》明确提供“Reg矢量计算宏函数内不同流水线之间的同步指令，目的流水线等待源流水线上所有指令完成才执行。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [asc_sync（同步）](../../apis/simd_api/c_api/sync/asc_sync.md)（`exemplifies`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《asc_sync（同步）》明确提供“等待所有流水线操作完成。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [同步控制](../../apis/simd_api/basic_api/reg_vector_compute/sync_control/sync_control.md)（`exemplifies`）：《同步控制》说明Reg矢量计算同步控制接口索引页，包含LocalMemBar。；《arch35 __aicore__ 调 LocalMemBar 报 507035》说明Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。。二者在Reg同步页的核心是LocalMemBar；C API AscMemBar和架构故障卡给出同一内存可见性合同与非法调用边界上存在可执行的直接衔接。
- [GE图模式263: 自定义VF Select被禁](ge_263_vf_select.md)（`related`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《GE图模式263: 自定义VF Select被禁》明确提供“MaskedFill kernel 用 __simd_vf__/asc_vf_call 自定义 VF 实现 Select，aclnn 预编译全绿但 GE 图模式 TBE 动态编译生成坏 binary 触发 AI Core error 263（aivec）；须跑图模式的 regbase kernel 中自定义 VF 路线 banned。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [__simd_vf__ if constexpr 致 hoisted 报错](simd_vf_if_constexpr_lowering_banned_exit_70.md)（`related`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《__simd_vf__ if constexpr 致 hoisted 报错》明确提供“dav-3510 上某 Reg __simd_vf__ 实现使用 if constexpr 与 constexpr trait 时，bisheng 后端报 Unsupported Inst must be hoisted 并退出 70；记录源码定位与编译边界，不提供未完成的 fallback 实现。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [simd_vf 互调导致 helper 编译失败](simd_vf_helpers_use_simd_callee.md)（`related`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《simd_vf 互调导致 helper 编译失败》明确提供“__simd_vf__ 函数不能直接调用另一个 __simd_vf__ helper；把被调 helper 标为 __simd_callee__ 后调用约束诊断消失。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [嵌套 VF 循环触发 bisheng stack smashing ICE](vf_bisheng_stack_smashing_ice.md)（`related`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《嵌套 VF 循环触发 bisheng stack smashing ICE》明确提供“Ascend950/arch35/CANN 9.1.0 下 __simd_vf__ 函数体内嵌套 while 循环调用 MicroAPI reg-compute 原语触发 bisheng INFERCHANNEL stack smashing ICE；扁平化为单层循环可消除。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
- [arch35 Select 异步SIMT同步失效致分支错选](../precision/arch35_select_simt.md)（`same_topic`）：arch35 Select 异步SIMT同步失效致分支错选 与《arch35 __aicore__ 调 LocalMemBar 报 507035》的实质衔接是：该卡定位 arch35 VSEL_CMPMASK_SPR 在异步 VF/同步原语缺失下读取陈旧 mask；RAW、跨调用/超64复用、Compare/Select 和同步 API 是可执行区分机制。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](../precision/arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《arch35 __aicore__ 调 LocalMemBar 报 507035》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 count Compare Select 异步VF 存读 RAW](../precision/arch35_count_compare_select_vf_raw.md)（`same_topic`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《arch35 count Compare Select 异步VF 存读 RAW》明确提供“Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
<!-- cannbot:related:end -->
