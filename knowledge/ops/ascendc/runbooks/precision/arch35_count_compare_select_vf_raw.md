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

- [LocalMemBar](../../apis/simd_api/basic_api/reg_vector_compute/sync_control/local_mem_bar.md)（`exemplifies`）：读写场景下，当读指令使用的寄存器和写指令使用的寄存器相同时，可以触发寄存器保序，指令将会按照代码顺序执行，不需要插入同步指令，而当使用的寄存器不同时，如果要确保读写指令顺序执行，则需要插入同步指令，写写场景同理。；arch35 count-based Compare 为 `__simd_vf__`、经 `Reg::StoreAlign/StoreUnAlign` (VEC_STORE) 写 bMask 且内部无 LocalMemBar；count-based Select 经 `Reg::LoadAlign<DIST_US>` (VEC_LOAD) 读 bMask（来源平台：950；证据等级: tool_observed）。通用依赖规则解释该 Compare 到 Select 的具体 RAW 隐患。
- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](select_vsel_cmpmask_spr_count_64.md)（`related`）：`Compare` 本身把完整掩码 per repeat 正确写入 bMask；错在 Select 的 VEC_LOAD 早于 Compare 的 VEC_STORE 提交；两卡区分了首段 mask 复用与 Compare→Select 异步存读 RAW 两种可并存故障，组成分层诊断链。
- [Select cmpmask 不偏移致分支反转诊断](select_cmpmask.md)（`related`）：非首块元素的分支选择被首块 mask bit 覆盖；Compare 后插 `bMask.GetValue(0)` 探针后 F1=2.5、F2=2.19 全过；两卡为同一 Compare→Select 精度链分别提供跨 repeat 复用与异步 VF 存读 RAW 的区分证据。
- [arch35 __aicore__ 调 LocalMemBar 报 507035](../compilation/arch35_aicore_localmembar_507035.md)（`related`）：原始轨迹卡记录“`Reg::LocalMemBar<VEC_STORE,VEC_LOAD>` 从 `__aicore__` 调用 → 运行时 507035 崩溃”；专项卡复现“从常规 `__aicore__` 函数直接调用违反调用约定，AIV 报 507035。”，后者提供调用上下文证据并把这一候选修法明确列为 banned。
- [arch35 Select 异步SIMT同步失效致分支错选](arch35_select_simt.md)（`same_topic`）：在 arch35 上用 `Compare`+`Select(VSEL_CMPMASK_SPR)` 做依赖性敏感的逐元素分支选择是禁用路线（无有效生产级同步手段保证 CMPMASK 在 vsel 前就绪，见 `## 失效边界`）。；mask 写入本身正确（GetValue 读回值正确），错在 Select 的 VEC_LOAD 早于 Compare 的 VEC_STORE 提交；任何不强制标量排空的 sync 都无法解决，需改走 mask 不出寄存器的 `__simd_vf__` Reg:: 融合实现（设计意图），或把 Compare/Select 包进同一 `__simd_vf__` 函数内并按需 `Reg::LocalMemBar<VEC_STORE,VEC_LOAD>`。；总览卡禁用该依赖链，RAW 专题卡把故障进一步落实为 count-based Compare 写 UB 与 Select 读 UB 的存读时序，并给出寄存器融合修复方向。
- [arch35 VSEL_CMPMASK_SPR 标量批跑 mask 污染](arch35_vsel_cmpmask_spr_mask.md)（`same_topic`）：VSEL_TENSOR_TENSOR_MODE：52/581 失败。；两模式都从 `bMask` UB 读 mask（不读陈旧 cmpmask SPR）→ 共享同一 VEC_STORE(Compare)→VEC_LOAD(Select) RAW。；小 count 实验表明切换 mode 仍有 52 个失败，RAW 专题解释两种 mode 都读 bMask UB，因此单纯换 mode 不能消除存读隐患。
<!-- cannbot:related:end -->
