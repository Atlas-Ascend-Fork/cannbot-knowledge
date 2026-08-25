---
type: "Runbook"
title: "arch35 count Compare Select 异步VF 存读 RAW"
description: "Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。"
tags: ["task.debugging", "topic.precision", "topic.implementation.synchronization", "topic.implementation.masking"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# arch35 count Compare Select 异步VF 存读 RAW

## 现象

在 Ascend950PR (arch35 / dav_c310，CANN 9.0.0-beta.2，RegBase 编程模型) 上调试 `softplus_v2_grad` 算子精度。C++ ST 跑小用例全过，但经 torch adapter (aclnn) 跑大批 L1 用例出现失败，失败全部落在 L1。失败 pattern 集中在「应走 sigmoid 分支 (`bx <= threshold`)、kernel 却给出 linear 分支 (`gradOutput`)」：

- 隔离复现 F1: `go=5, self=0, beta=1, thr=20`。`bx = beta*self = 0`，`mask = (bx > thr) = (0 > 20) = false`，应取 `grad_sig = sigmoid(0)*5 = 2.5`。Golden=2.5，Actual=5（linear）。`mismatch=1/1`。
- F2: `bx=1, thr=20`，`mask=false`，Golden=2.19(sigmoid)，Actual 与 linear 一致。
- mask=true 用例（`bx > thr`）linear 分支正确，未失败。

即：`mask=false` 时 Select 本应选 `src1=grad_sig`，却选了 `src0=gradOutput`——等价于 Select 把 mask 读成了 true。

kernel `ComputeFp32Core` 在 fp32 路径用 `AscendC::Compare<float,uint8_t>(bMask, bBx, bThr, GT, count_padded)` 生成 packed mask，中间夹 Maxs/Mins/Exp/Adds/Div/Mul 一串 async VF 算术（各带 `PipeBarrier<PIPE_V>`），最后 `AscendC::Select(bBx, bMask, bG, bThr, VSEL_CMPMASK_SPR, count_padded)` 做 `where(mask, gradOutput, grad_sig)`。设计意图是把 Compare→Select 作为可融寄存器链组合，整链融进一个 `__simd_vf__` VF 调用，mask 全程留 MaskReg、不做 UB 往返；实现偏离设计，改用分离的同步 Level2 API + `PipeBarrier`，中间 mask 落 UB，且 Select 用 `VSEL_CMPMASK_SPR` 而非设计的 `VSEL_TENSOR_TENSOR_MODE`。

## 适用场景

- **工程形态**：kernel 直调（RegBase 编程模型，`__aicore__` 常规函数内调用 `AscendC::` Level2 vector API，非 `__simd_vf__` 融合体）。
- **API 路径**：`AscendC::Compare<T,MaskT>(dst, src0, src1, CMPMODE::GT, count)` (count-based Level2) → `AscendC::Select(dst, selMask, src0, src1, SELMODE, count)` (count-based Level2)；CANN 头 `dav_c310/kernel_operator_vec_cmpsel_impl.h`、`dav_c310/kernel_operator_vec_sel_impl.h`。
- **验证过的平台与 CANN 版本**：Ascend950PR (arch35/dav_c310)，CANN 9.0.0-beta.2。仅本平台实测，`platforms: [950]`。
- **适用粒度**：`operator_family`（适用于 arch35 上任何使用 count-based Compare→Select 且 Select 经 LoadAlign 读 bMask UB 的算子，不限 softplus_v2_grad）。
- **路线优先级**：`recommended_fastpath`（确诊后应改走 `__simd_vf__` Reg:: 融合实现，mask 留在 MaskReg 不做 UB 往返，本卡给出判别方法；正向修复配方）。
- **不适用或未验证场景**：repeat-based Compare (`mask[]` 重载) 内部带 `SetFlag<V_S>/WaitFlag<V_S>` 不在本卡范围；非 arch35 平台 (a2/a3) 未验证，推断行为不同，见 `## 失效边界`。

## 判别方法

**触发 (trigger)**：arch35 算子精度失败，失败用例集中在「条件分支应取 src1 却取了 src0」，且 C++ ST 小用例可能全过、大规模 L1 才暴露；同一用例多次跑结果不稳定（数据/时序依赖，呈现 heisenbug 特征）。

**可执行探针 (probe)**：在 `Compare` 之后、`Select` 之前，插入一次 `bMask.GetValue(0)`（标量同步读，必要时包一层 PRINTF 以防 release 优化移除孤立 GetValue 的排空效应）：

```cpp
// 诊断探针：标量排空，强制 async VF 的 VEC_STORE 对后续 VEC_LOAD 可见
uint8_t probe = bMask.GetValue(0);
```

重编重跑隔离用例（F1/F2）。若加探针后由失败转通过、移除即复现，则确诊为 async-VF mask 存读隐患，而非逻辑错。

**原始观测 (observation)**（本 trace 实测）：
- 加 PRINTF（含 `bBx.GetValue(0)/bG.GetValue(0)/bMask.GetValue(0)`）后 F1=2.5、F2=2.19 全过，`mask0=0(false)/255(true)` 与正确语义一致。
- 移除探针即复现失败。
- `bMask.GetValue(0)` 读回 0(false)/255(true) 与正确语义一致——证明 Compare 写入本身正确，错在 Select 的 VEC_LOAD 早于 Compare 的 VEC_STORE 提交。

**解释 (interpretation，机制链归因)**：
1. arch35 (dav_c310) 的 count-based `Compare` (`CompareScalarLevel2`) 是 `__simd_vf__` 异步，经 `Reg::StoreAlign/StoreUnAlign` (VEC_STORE) 把 packed mask 写入 `bMask` UB，函数内部**无** `LocalMemBar`。
2. count-based `Select` (`SelectMode0Level2` / `SelectMode2Level2`) 经 `Reg::LoadAlign<U, DIST_US>(selMask, sel)` (VEC_LOAD) 从 `bMask` UB 读 mask：

```cpp
// SelectMode0Level2 (VSEL_CMPMASK_SPR), sizeof(T)==4:
Reg::LoadAlign<U, Reg::MaskDist::DIST_US>(selMask, sel);   // 循环前一次性载入 bMask
Reg::MaskUnPack(selMask, selMask);
for (i in repeatTime) {
    ... Reg::Select(dstReg, src0Reg, src1Reg, selMask);     // 复用载入的 selMask
}
// SelectMode2Level2 (VSEL_TENSOR_TENSOR_MODE), sizeof(T)==4:
for (i in newRepeatTimes) {
    Reg::LoadAlign<uint8_t, DIST_US>(tmpMask0, sel + i * selOffset);  // 逐轮载入
    Reg::MaskInterleave(selMask0, selMask1, ...);
    ...
}
```

两模式都从 `bMask` UB 读 mask（不读陈旧 cmpmask SPR）→ 共享同一 VEC_STORE(Compare)→VEC_LOAD(Select) RAW。
3. kernel 自带注释点明根因前提：arch35 `asc_vf_call` 底层为 async SIMT，无 `asc_sync_vec` 同步原语，传统 `V_MTE3` flag 无法捕获 async SIMT VF 完成。
4. `AscendC::PipeBarrier<PIPE_V>`（含升级到 `PIPE_ALL`）只序化 V-pipe 指令顺序，**不**刷新 async-VF 的 VEC_STORE 提交缓冲使后续 VEC_LOAD 可见；Compare→Select 重排相邻去掉全部中间算术后仍失败，排除「中间算术干扰 bMask store buffer」。
5. `LocalTensor::GetValue` 走标量 (S) 管同步读，排空全部 V 写并使其全局可见 → mask 可见 → Select 读对。

**判别结论**：mask 写入本身正确（GetValue 读回值正确），错在 Select 的 VEC_LOAD 早于 Compare 的 VEC_STORE 提交；任何不强制标量排空的 sync 都无法解决，需改走 mask 不出寄存器的 `__simd_vf__` Reg:: 融合实现（设计意图），或把 Compare/Select 包进同一 `__simd_vf__` 函数内并按需 `Reg::LocalMemBar<VEC_STORE,VEC_LOAD>`。

## 系统信息

- 工具链：CANN 9.0.0-beta.2（`~/Ascend/cann-9.0.0-beta.2`），bisheng clang 15.0.5。
- 目标平台：Ascend950PR / arch35 / dav_c310。
- 编程模型：RegBase。
- 相关文件（与 trace 事件读写一一对应）：
  - `op_kernel/arch35/softplus_v2_grad_kernel.h`（`ComputeFp32Core`、`Process`）
  - `op_host/arch35/softplus_v2_grad_tiling_arch35.cpp`、`op_host/softplus_v2_grad_infershape.cpp`、`op_host/softplus_v2_grad_def.cpp`
  - CANN 头：`x86_64-linux/asc/impl/basic_api/dav_c310/kernel_operator_vec_cmpsel_impl.h`、`.../dav_c310/kernel_operator_vec_sel_impl.h`、`.../reg_compute/dav_c310/kernel_reg_compute_vec_cmpsel_impl.h`、`.../reg_compute/kernel_reg_compute_membar_intf_impl.h`
  - 参考 op：`hard_swish_grad_v2`（`opp/built-in/op_impl/ai_core/tbe/impl/ops_nn/ascendc/hard_swish_grad_v2/`），`SoftmaxFlashNDImpl` (`.../adv_api/detail/activation/softmax/regbase/c310/softmax_flash_impl.h`)

## 设计决策

- 设计意图：`gradInput = where(mask, gradOutput, grad_sig)` 用 Select 模式 2 (`VSEL_TENSOR_TENSOR_MODE`)，并把 Compare→Select 列为可融寄存器链组合 (S6→S7)，整链 S1–S7 融进一个 `__simd_vf__` VF 调用，mask 全程留 MaskReg、不做 UB 往返。
- 实现偏离设计两处：(1) 未做 VF 融合，改用分离的同步 Level2 API + `PipeBarrier`，中间 mask 落 UB；(2) Select 用 `VSEL_CMPMASK_SPR` 而非设计的 `VSEL_TENSOR_TENSOR_MODE`。本 trace 证明 mode 0/2 都读 bMask UB（同一 RAW），故 mode 偏离不是根因，未融合 + 无 sync 才是根因。
- 被放弃的修复尝试（佐证判别结论）：`Reg::LocalMemBar<VEC_STORE,VEC_LOAD>` 从 `__aicore__` 调用 → 运行时 507035 崩溃（`Reg::LocalMemBar` 为 `__simd_callee__`，需 `__simd_vf__` 调用上下文）；Compare→Select 重排相邻 → 仍失败。两者均未恢复完整 after 代码，after/closure not recovered from trace。

## 验证信号

> 来源：本 trace 在 Ascend950PR + CANN 9.0.0-beta.2 上对 `softplus_v2_grad` 的隔离复现与 CANN 头文件检查。

- L1 torch 跑批 578 总/462 pass/116 fail，失败集中在 mask=false 用例（来源平台：950；证据等级: tool_observed）
- 隔离 F1 Golden=2.5(sigmoid) Actual=5(linear)；mask=true 用例 linear 正确（来源平台：950；证据等级: tool_observed）
- Compare 后插 `bMask.GetValue(0)` 探针后 F1=2.5、F2=2.19 全过；移除即复现（来源平台：950；证据等级: tool_observed）
- `bMask.GetValue(0)` 读回 0(false)/255(true) 与正确语义一致，证明 Compare 写对、Select 读陈旧（来源平台：950；证据等级: tool_observed）
- arch35 count-based Compare 为 `__simd_vf__`、经 `Reg::StoreAlign/StoreUnAlign` (VEC_STORE) 写 bMask 且内部无 LocalMemBar；count-based Select 经 `Reg::LoadAlign<DIST_US>` (VEC_LOAD) 读 bMask（来源平台：950；证据等级: tool_observed）

## 失效边界

- repeat-based Compare (`mask[]` 重载) 内部带 `SetFlag<V_S>/WaitFlag<V_S>`，不在本卡结论范围；若改用 repeat-based Compare + Select 可能规避该隐患，但本 trace 未验证。
- 非 arch35 平台 (a2/a3) 未验证，推断可迁移性低——async-VF 语义与 `asc_sync_vec` 原语可用性随 arch 不同；**未验证，推断可迁移**。
- 本卡只判别隐患与机制，不含正向修复的完整 after 代码（trace 以 workspace 回退收尾，未提交修复）。

## 坏实践

- 用 PRINTF/GetValue 当生产 sync：GetValue 是调测接口，release 优化可能移除其排空效应（本 trace 观察到 bare `GetValue(0)` 在 restructured release build 不排空），不可作为修复手段。
- 仅切换 `VSEL_CMPMASK_SPR`↔`VSEL_TENSOR_TENSOR_MODE` 当作修复（两模式都 LoadAlign bMask，不解决 RAW）。
- 仅升级 `PipeBarrier<PIPE_V>`→`<PIPE_ALL>` 或重排 Compare→Select 相邻当作修复（均不排空 async-VF store→load）。

## 误诊

- 早期一度据「Actual ≈ 0.5×Golden」猜测 sigmoid 算错（常数 0.25 vs 0.5）；隔离复现后否定——sigmoid 算术链 (Muls→Exp→Adds→Div→Mul) 在 mask=true 与全 sigmoid 用例均正确，错只在 Select 取分支（agent_reported 假设，已否定）。
- 早期据设计偏离猜测「mode 0 是 bug、切 mode 2 即解」；实测 mode 2 单切不修复（两模式同读 bMask UB）（agent_reported 假设，已否定）。
- 早期猜测「中间 async VF 算术 (Maxs/Mins/Exp/...) 干扰 bMask store buffer」；重排 Compare→Select 相邻去掉全部中间算术后仍失败，排除（agent_reported 假设，已否定）。

<!-- cannbot:related:start -->
## 相关

- [AscSelect](../../apis/simd_api/c_api/reg/compare_and_select/asc_select.md)（`exemplifies`）：AscSelect：AscSelect 的 cmpmask 设置/读取和三输入别名约束直接决定结果；所选 runbook均针对该接口的 >64 掩码复用、跨调用残留、异步 RAW 或 dst/src 别名失效，而非泛化连接所有比较接口。 目标卡《arch35 count Compare Select 异步VF 存读 RAW》补充：Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW
- [Compare](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/compare.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《Compare》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [Compare](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/compare.md)（`exemplifies`）：该 runbook 展示 Compare 结果跨异步 VF 未完成即被 Select 读取造成 RAW 错选。
- [LocalMemBar](../../apis/simd_api/basic_api/reg_vector_compute/sync_control/local_mem_bar.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《LocalMemBar》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [PipeBarrier](../../apis/simd_api/basic_api/sync_control/intra_core_sync/pipe_barrier_isasi.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《PipeBarrier》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [Select](../../apis/simd_api/basic_api/memory_vector_compute/compare_and_select/select.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《Select》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/select.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW说明Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。
- [Select](../../apis/simd_api/basic_api/reg_vector_compute/mask_reg_compute/select.md)（`exemplifies`）：《Select》的任务是“根据mask的比特位值从src0或src1中选取元素，bit为1选src0，bit为0选src1。”。《arch35 count Compare Select 异步VF 存读 RAW》具体提供“Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。”，它直接用于Reg Select 的 mask 来源、CMPMASK 生命周期、偏移、别名和跨调用污染。
- [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《SetFlag/WaitFlag》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [SetFlag/WaitFlag](../../apis/simd_api/basic_api/sync_control/intra_core_sync/set_flag_wait_flag_isasi.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《SetFlag/WaitFlag》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [VF调用](../../apis/simd_api/basic_api/reg_vector_compute/vf_call/vf_call.md)（`exemplifies`）：Compare/Select 异步 VF 案例说明连续 asc_vf_call 的生产者写和消费者读之间若缺少完成屏障会出现 RAW 精度错误。
- [asc_sync（同步）](../../apis/simd_api/c_api/sync/asc_sync.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW 与《asc_sync（同步）》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [比较与选择](../../apis/simd_api/basic_api/reg_vector_compute/compare_and_select/compare_and_select.md)（`exemplifies`）：arch35 count Compare Select 异步VF 存读 RAW说明Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。
- [GE图模式263: 自定义VF Select被禁](../compilation/ge_263_vf_select.md)（`related`）：raw VF 案例给出 Compare+Select 的 mask 生成和消费细节，可核对 Select 代码本身而非把 263 仅归因于 GE。
- [Select CMPMASK_SPR 模式致混合分支误选](select_cmpmask_spr.md)（`related`）：目标卡定位 Compare 写 mask UB 到 Select 读 mask UB 的 VF RAW；本卡定位 SPR mode 内 repeat 指针不推进，barrier 是否改变失败可区分两条机制。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`related`）：候选处理 Compare 生产 mask 与 Select 消费间缺 VF RAW；本卡先证明 bMask 正确再定位地址复用。
- [arch35 Select VSEL_CMPMASK_SPR 每 64 元素复用](arch35_select_vsel_cmpmask_spr_mask_reuse_count_over_64.md)（`related`）：该卡展示同一 VF 中计数 Compare/Select 生产消费的 RAW 风险；即使分段长度正确，也需保证每段 mask 在覆写前被消费。
- [arch35 Select cmpmask SPR 跨调用泄漏致非确定失败](arch35_select_cmpmask_spr.md)（`related`）：arch35 Select cmpmask SPR 跨调用泄漏致非确定失败 与《arch35 count Compare Select 异步VF 存读 RAW》的实质衔接是：这些卡都围绕 arch35 VSEL_CMPMASK_SPR 的生成、复用、偏移或跨调用污染；Set/GetCmpMask 是直接控制和观察该 SPR 状态的接口。
- [arch35 Select 超64 cmpmask 残缺判别](arch35_select_64_cmpmask.md)（`related`）：该卡证明 count-based Compare 写 UB mask 到 Select 读回之间还可能存在 VEC_STORE→VEC_LOAD RAW，可用 GetValue 探针与周期错位模式区分。
- [Duplicate 全量清零 padding 覆盖有效区 banned](duplicate_padding_banned.md)（`same_topic`）：Duplicate 全量清零 padding 覆盖有效区 banned 与《arch35 count Compare Select 异步VF 存读 RAW》的实质衔接是：该故障同时受 Duplicate 无 offset 契约、Select 模式2 连续 mask 消耗和 padding 有效计数控制；所连卡都直接用于清理 padding 而不覆盖有效区或复现 cmpmask 污染。
- [VF 归约落 UB 后 GetValue 读取陈旧标量](vector_scalar_ub_handoff_requires_explicit_completion.md)（`same_topic`）：arch35 count Compare Select 异步VF 存读 RAW 与《VF 归约落 UB 后 GetValue 读取陈旧标量》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：arch35 count Compare Select 异步VF 存读 RAW 与《arch35 Select 异步SIMT同步失效致分支错选》的实质衔接是：该故障是 count Compare 将 packed mask 异步写 UB、随后 Select 重新 Load 的 VEC_STORE→VEC_LOAD RAW；GetValue 探针、LocalMemBar/pipe 同步边界和准确 Compare/Select 接口共同支持确诊与修复。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染 与《arch35 count Compare Select 异步VF 存读 RAW》的实质衔接是：该卡锁定标量/小 count 的 packed mask 仅写少量字节而 Select 载入 stale padding；跨调用、超64、RAW、Compare/Select、GetValue 与同步材料提供可执行区分。
- [arch35 __aicore__ 调 LocalMemBar 报 507035](../compilation/arch35_aicore_localmembar_507035.md)（`same_topic`）：《arch35 __aicore__ 调 LocalMemBar 报 507035》处理“Ascend950PR (arch35/dav_c310) 上 Reg::LocalMemBar<VEC_STORE,VEC_LOAD> 是 __simd_callee__ 函数，须在 __simd_vf__ (VF) 调用上下文内使用；从常规 __aicore__ kernel 函数直接调用触发运行时 507035 (AIV 错误)。本 trace 两次独立调用（旧 4-buffer 代码、新 5-buffer 重排代码）均 507035。作为 count-based Compare→Select mask 隐患的最小 sync 修复手段 banned。”。《arch35 count Compare Select 异步VF 存读 RAW》明确提供“Ascend950PR (arch35/dav_c310) 上 count-based AscendC::Compare 经异步 VF VEC_STORE 写 packed mask 到 bMask UB，内部无 LocalMemBar；随后 count-based AscendC::Select 经 Reg::LoadAlign<DIST_US> (VEC_LOAD) 读 bMask，构成 VEC_STORE→VEC_LOAD RAW 隐患。PipeBarrier 不排空该隐患，仅 LocalTensor::GetValue 标量排空可使 mask 可见。表现为 mask=false 用例 Select 取 linear(gradOutput) 而非 sigmoid(grad_sig)，精度失败。”，其参数、调用或验证步骤直接接入LocalMemBar 507035 的 Compare/Select 调用触发、屏障约束和可执行替代。
<!-- cannbot:related:end -->
