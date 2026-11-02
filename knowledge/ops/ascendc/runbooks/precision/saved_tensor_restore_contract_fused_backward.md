---
type: Runbook
title: "融合反向的保存状态：核对 max/sum、原输出 O 与因果掩码合同"
description: "区分逐行逻辑统计与固定 CANN 接口的物理布局；保留原保存 O，核对单 LSE 适配及矩形因果掩码，不把源码可达当实测等价。"
tags:
- task.design
- topic.architecture
status: draft
sources:
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_api/aclnn_flash_attention_score_grad.cpp
    role: primary
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_host/arch35/flash_attention_score_grad_tiling_common_regbase.cpp
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch35/vector_api/pse_atten_mask_muls_simple_softmax.h
    role: implementation
  - resource: https://gitcode.com/cann/ops-transformer/blob/be33d95bb755cedec3108f70805c1874d1792540/attention/flash_attention_score_grad/op_kernel/arch35/vector_api/vf_muls_sel_simple_softmax.h
    role: implementation
created_at: "2026-09-16T00:00:00Z"
updated_at: "2026-10-22T04:11:00Z"
platforms: ["950"]
aliases: ["CAND-FAG-3", "attention backward saved LSE max sum"]
---

> **来源范围**：历史配方来自车队私有观测，仍为 draft。下节新增约束来自所列固定提交的公开源码，只认证该版本的接口与分支，不追认历史性能、确定性或当前运行库等价。
# 融合反向的保存状态：核对 max/sum、原输出 O 与因果掩码合同

## 固定版本的接口边界（源码事实，未新增设备验证）

将只保存原生 dtype 输出 O 和 FP32 logsumexp 的反向任务对应到公共 CANN 接口时，先逐项绑定保存状态，不能仅因公式同属 attention backward 就直接换成融合调用。

- 在上述提交的 `aclnnFlashAttentionScoreGradV4GetWorkspaceSize` 中，`attentionInOptional` 虽带 Optional 后缀，入口仍拒绝空指针。应保留任务实际提供的 O；不要为了配合接口重跑前向并偷偷换掉已舍入的 O。这里的入口检查本身不证明任意 O 都具有正确语义。
- arch35 的 `CheckDtypeValid` 调用 `CheckSoftmaxDtype`，缺少 max 或 sum 描述就返回失败，二者都须为 FP32。`CheckSoftmaxMaxShape` / `CheckSoftmaxSumShape` 对非量化、非 TND 路径要求物理形状 `[B,H,Sq,8]`；量化分支末维为1。逐行一个逻辑统计量不代表可以向该接口传末维1。
- 此 V4 签名没有单个 LSE 参数。device 的 `MulsSelSimpleSoftMax` 路径消费 max/sum，按减 max、exp、除 sum 重建概率。实数恒等式 `LSE=max+log(sum)` 不证明某种合成状态与原 FP32 LSE 在该实现中数值等价；这是需独立声明和验证的适配问题，不是数学上不可能。
- `ProcessTokensInfo` 对非 TND 的 right-down causal 校正出 `nextToken=Sk-Sq`。同一函数在 mask 为空时又把两个 token 窗口重置为最大值；不能只传 sparse-mode 标签和空 mask 就宣称保留因果语义。矩形任务应另核实际 mask 表示和边界，方阵通过不覆盖矩形。

处置顺序是固定任务原输入及保存状态、核实所选接口/tiling/device 的完整消费链，再设计具名适配并按原完整分母验证全部梯度。这里未实现状态适配、未构建或调用 CANN、未取得新 P/F；公开提交到某个实际 provider 二进制的映射也须单独核验。下文为历史逻辑配方与示意代码，不是该公共接口物理形状或 DataCopy 重载的可直接复制实现。

## 适用场景

- 适用平台与范围：soc=Ascend910_V220 / Ascend950PR；cann=9.0.0+；op_class=fused_backward_with_recompute / flash_attention_backward / online_softmax_backward / 前向已产出逐行归一化统计的任何反向算子。
- 验证来源：cann ops-transformer flash_attention_score_grad/op_kernel/arch35/（反向 kernel 以 Init 参数接收 softmaxMax/softmaxSum GM 指针，2026-05-10）；a5_ops 未验证（unverified_on）。

## 候选（未验证 —— 默认检索不返回,需 --status all 才可见）

`applies_to: soc=Ascend910_V220 / Ascend950PR; cann=9.0.0+; op_class=fused_backward_with_recompute / flash_attention_backward / online_softmax_backward / any_bwd_op_whose_fwd_emitted_per_row_normalization_state`
`derived-from: cann-source (fa-grad-class backward, 2026-05-10 multicann)`
`verified_on: cann ops-transformer flash_attention_score_grad/op_kernel/arch35/ — backward kernels accept `softmaxMax` and `softmaxSum` GM pointers as Init arguments and consume them via a per-tile CopyInMaxSum helper (declared in `vector_api/pse_atten_mask_muls_simple_softmax.h`); double-buffered max-sum queue `maxSumQue[2]` indexed by `taskId & 1` is the hot-loop shape in three peer block-vec headers (the s1s2_bn2_regbase, s1s2_bn2gs1s2_regbase, and s1s2_bn2s2_regbase main-vec headers all use the same `CopyInMaxSum<T2, VECTOR_BASEM>(..., maxSumQue[taskId & 1], softmaxMaxGm, softmaxSumGm)` call shape)`
`unverified_on: a5_ops`

**Trigger**: A fused backward op needs intermediate per-row statistics that were computed once in the forward pass — specifically the online-softmax running max and running sum (CAND-FA2's `runMax`, `runSum`). Re-computing these in the backward kernel would require replaying the full forward streaming softmax over QKᵀ, doubling forward-matmul work. The fwd already had them in registers/UB at end-of-row; the contract is to persist them to GM as auxiliary outputs of the forward and let the backward re-read them.

**Recommendation**: Treat the (max, sum) pair as a **first-class fused-op output**, not an internal scratch. Persistence contract:

1. **Forward emits two extra GM tensors**, shape `[B, N, S1, 1]` (or `[T, N, 1]` in TND) — one for the per-row running max, one for the per-row running sum. These are public-API outputs allocated by the user/host, NOT in the opaque workspace (P-P89 contract: workspace is for scratch the user cannot inspect; saved-tensor for backward is a PUBLIC saved-tensor in PyTorch terms).
2. **Backward Init signature** accepts both pointers explicitly (`softmaxMax`, `softmaxSum`) alongside dy and the original Q/K/V — this is the structural marker that the bwd is a recompute-with-saved-tensors variant, NOT a full-replay variant.
3. **Inside the bwd hot loop**, copy-in the (max, sum) row-strip for the current tile using a double-buffered VECIN queue indexed by `taskId & 1`. Use `DataCopyPad` because the row-strip width is `VECTOR_BASEM` (e.g. 64) which may not align to 32B at the trailing tile. The copy-in runs concurrently with the prior tile's cube matmul thanks to the `& 1` ping-pong index.
4. **Apply** the saved (max, sum) inside the bwd's `simpledSoftmax` block (the recompute of P = softmax(scale·Q·Kᵀ + bias)): `p = exp(scores - max[row]) * (1.0f / sum[row])` — using Brcb to broadcast the per-row scalar across the row's columns, then VEC Exp/Sub/Mul.

**Concrete anchor** (public AscendC):
```cpp
// Forward (emit side) — at row-group epilogue, after final runMax / runSum are computed:
DataCopy(softmaxMaxGm[rowGroupOffset], runMaxUb, vectorBaseM);   // [VECTOR_BASEM] per row
DataCopy(softmaxSumGm[rowGroupOffset], runSumUb, vectorBaseM);

// Backward (consume side) — declare ping-pong queue at Init:
TQue<QuePosition::VECIN, 2> maxSumQue;   // depth-2 double buffer
pipe->InitBuffer(maxSumQue, 2, vectorBaseM * 2 * sizeof(float));  // max+sum interleaved

// Per-tile copy-in indexed by taskId
LocalTensor<float> ms = maxSumQue.AllocTensor<float>();   // implicit ping/pong by depth-2
DataCopyExtParams cp{1, (uint32_t)(vectorBaseM * sizeof(float)), 0, 0, 0};
DataCopyPadExtParams<float> pad{};
DataCopyPad(ms,                         softmaxMaxGm[curRowOffset], cp, pad);
DataCopyPad(ms[vectorBaseM],            softmaxSumGm[curRowOffset], cp, pad);
maxSumQue.EnQue(ms);
// ... in the recompute stage, dequeue and use ms[0..VECTOR_BASEM-1] (max) and ms[VECTOR_BASEM..2·V-1] (sum) ...
LocalTensor<float> ms2 = maxSumQue.DeQue<float>();
LocalTensor<float> maxRow = ms2;
LocalTensor<float> sumRow = ms2[vectorBaseM];
// Brcb broadcast across columns, then Sub/Exp/Mul to reconstruct P from the saved stats
```

**Why it works**:
- Saving just `[B,N,S,1]` adds <1% to forward GM traffic (the softmax denominator is one scalar per row, NOT per column) — the bwd otherwise pays a full re-reduction over S2 to find max/sum
- Public outputs (not workspace): the fwd op promises these as part of its contract, so the bwd can be invoked by a different launch / different stream and still find the data
- Double-buffer queue depth-2 with `taskId & 1` indexing is the standard CV-decoupling shape — the (max, sum) copy-in runs on AIV while the prior tile's QKᵀ runs on AIC
- `DataCopyPad` not `DataCopy`: row counts (`VECTOR_BASEM`, typically 64) are 32B-aligned for fp32, but the last row-group of TND / variable-S can be short — pad-with-zero is the only safe primitive

**Determinism**: Deterministic by construction — the saved (max, sum) is bit-identical to what the forward computed (it's the same bytes, just persisted to GM rather than discarded). The bwd's reconstruction `exp(scores - max) / sum` is element-wise so per-tile order does not matter. Combine with CAND-FAG-2 to get full backward determinism.

**Other instances predicted**:
- LayerNorm / RMSNorm backward: fwd saves per-row mean+rstd; bwd reads them instead of recomputing
- Cross-entropy + log-softmax fused backward: fwd saves per-row log-sum-exp; bwd reads to reconstruct probabilities
- Online-softmax-and-rescale chains: any second-pass that needs to know the final max/sum from the first pass
- Group-norm backward: fwd saves per-group mean+rstd
- BatchNorm-train backward: fwd saves per-channel running stats (already standard PyTorch behavior — this candidate codifies the AscendC pipe-pong copy-in shape)

**Risks before promotion**:
- a5_ops has no shipped fused-bwd op yet; the saved-tensor I/O cost vs recompute cost has not been measured on this codebase. For very short S (< 256), recompute may be cheaper than the extra GM round-trip
- The contract is **fragile across fwd↔bwd version skew**: if the fwd op's online-softmax algorithm changes (different center-max convention, different scale application order), the saved tensor becomes invalid for an old bwd. Version-tag the saved tensor or pin fwd/bwd to the same kernel build
- Memory footprint: `[B,N,S,1]` fp32 is small but non-zero — for B=32, N=32, S=8192, two tensors = 64MB. Fine for training, may be too much for inference if the bwd is being used for gradient checkpointing
- `DataCopyPad` with non-zero `paddingValue` is dangerous if the bwd reads beyond the valid row count — always pair with explicit `s1RealSize` bookkeeping

**Cross-reference**:
- CAND-FA2 (online-softmax per-row state recurrence): this candidate is the BACKWARD half — CAND-FA2 describes what the fwd computes and HOLDS in registers; this candidate describes how those values cross the fwd↔bwd boundary via saved tensors
- P-P89 (workspace contract for fused ops): related but DIFFERENT — saved tensors for backward are PUBLIC outputs (user can inspect, must be stable across versions), workspace is OPAQUE. The fwd's signature must list `softmaxMax` and `softmaxSum` as outputs, not bake them into `workspace`
- CAND-FAG-1 (three-kernel pre/main/post split): orthogonal — saved-tensor restore happens in MAIN, the pre/main/post split is about how the bwd's outputs are written
- CAND-FA1 (manual cross-core flag handoff): orthogonal

**Promote when**: a5_ops ships a paired (fwd, bwd) fused op pair where the bwd reads fwd-emitted saved tensors AND shows <30% slowdown vs a hand-written non-fused PyTorch backward AND the saved-tensor GM round-trip is profiled to confirm <10% of bwd wall time.

<!-- 迁移自 porter kb/target/ascendc/patterns/unverified/candidates.md（CAND-FAG-3，convert_cand_to_okf.py）。status=stub 未验证,待复现后 promote。 -->
