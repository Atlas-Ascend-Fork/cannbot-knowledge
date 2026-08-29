---
type: Runbook
title: indexer / 块量化 AscendC kernel 的非有限值 (NaN/Inf) 污染防护
description: indexer / 块量化 AscendC kernel 的非有限值 (NaN/Inf) 污染防护。在昇腾 AscendC 上写 Lightning-Indexer 稀疏选择 / 动态块量化 kernel 时，输出整块变废、稀疏索引不可预期。根因常是 kernel 内的规约 / 排序算子直接吃到了非有限值 (NaN/Inf)——IEEE 语义下一个 NaN 就能污染整块规约结果或让排序次序未定义。这类精度问题不 crash、只错值，需在算子内主动剔除非有限值。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/433
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/28
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# indexer / 块量化 AscendC kernel 的非有限值 (NaN/Inf) 污染防护

## 适用场景

在昇腾 [AscendC](../../concepts/frameworks/ascendc.md) 上写 [Lightning-Indexer](../../concepts/kernels/lightning_indexer.md) 稀疏选择 / 动态块量化 kernel 时，输出整块变废、稀疏索引不可预期。根因常是 kernel 内的**规约 / 排序算子直接吃到了非有限值 (NaN/Inf)**——IEEE 语义下一个 NaN 就能污染整块规约结果或让排序次序未定义。这类精度问题不 crash、只错值，需在算子内主动剔除非有限值。

## 陷阱 1：块量化的 scale 用 ReduceMax(abs(x)) 前必须剔除非有限值

动态 per-block 量化的每块 scale = 块内 `max(|x|)`。`ReduceMax` 遵循 IEEE 语义：块内任一 lane 为 NaN，规约即 NaN → scale=NaN → 该块所有量化输出被污染。裸 `Abs(x)` 后直接 `ReduceMax` 不筛非有限值就会中招。修法是「先算非有限 mask、再带 mask 求 Abs（非有限 lane 归 0）」：

```cpp
Muls(xAbs, x, 0.0f, preg);                          // 有限→0, NaN/Inf→NaN (Inf*0=NaN)，廉价探测器
Compare<float, CMPMODE::NE>(cmp, xAbs, xAbs, preg); // x!=x 仅 NaN 为真 → 非有限 mask（AscendC 上 isnan 标准写法）
MaskNot(cmp, cmp, preg);                            // 取反 → 有限 lane mask
Abs(xAbs, x, cmp);                                  // 仅有限 lane 求 |x|，非有限 lane ZEROING 归 0
ReduceMax(scale, xAbs, preg);                       // 块 max 不再被 NaN/Inf 污染
```

要点：`Muls(t, x, 0)` 同时覆盖 NaN 与 Inf（`Inf*0=NaN`）；`Compare<NE>(t, t)` 自比较不等仅 NaN 为真；`MaskNot` 后作 `Abs` 的谓词 + ZEROING 归并，把非有限 lane 变 0 排除出 `ReduceMax`。改后块内出现 NaN/Inf 时 scale 仍由有限值的 `max(|x|)` 决定。

## 陷阱 2：不要让 TopK 打分输入含 NaN（排序对 NaN 为未定义行为）

量化版 Lightning-Indexer 的 TopK 过程对 NaN 的排序是**未定义行为**（算子规格明载）——NaN 参与排序时相对次序不确定，会使 topk 选出的稀疏 block/token 索引不可预期、破坏稀疏注意力的选择正确性。因此**不要让进入 TopK 的打分矩阵包含 NaN**。相关约束（同规格）：`W ⊙ Scale_Q` 的结果须可被 float16 表示、`query_dequant_scale` / `key_dequant_scale` 须 ≥ 0；违反这些或让反量化中间量出现 inf/NaN，正是把 NaN 引入 topk 输入的来源。

## 可迁移原则

凡 kernel 内对激活做**规约（ReduceMax/ReduceSum）或排序（TopK）**、而上游可能因反量化 / 溢出产生非有限值的路径，都要在进规约/排序前用「乘 0 自比较 NE 得非有限 mask → ZEROING 归并」显式剔除 NaN/Inf；量化 scale 求解尤其如此（一个坏 lane 污染整块）。低比特量化路径把激活的动态范围压得很窄，反量化中间量更易越界产生 inf/NaN，这类防护不是可选项。压 Lightning-Indexer 单算子时延切量化算子的做法见 [quant-lightning-indexer-latency](../../optimizations/experience/rules/quant_lightning_indexer_latency.md)；稀疏 attention 的变长零长度边界见 [precision-sparse-attention-kernel-boundary-golden](precision_sparse_attention_kernel_boundary_golden.md)。

## 参考实现及其约束

- 陷阱 1 参考实现：cann-recipes-infer 的 `indexer_compress_epilog` / `kv_compress_epilog` 的 `VFProcessDynamicBlockQuant`（fp16/bf16 → fp8_e5m2/fp8_e4m3fn 动态块量化，目标平台 [ascend950](../../concepts/platforms/ascend_950.md)）；本 diff 该保护仅落在尾块循环，主循环体是否已有同等处理未核。
- 陷阱 2 参考实现：cann-recipes-infer 的 `LightningIndexerQuant` 算子规格文档；该 UB 约束记录于量化版规格，非量化版共享 topk 机制。
- 边界：适用面限定到「以 `ReduceMax(abs(x))` 求块 scale 的 AscendC 量化 kernel」与「Indexer 量化 TopK」，不外推到整栈。

## 相关经验

- 另见 [AscendC kernel 用无符号整型算有效长度：负差下溢 + Max(x,0) 对无符号是空操作 → 无效 / 短行 aic error](../runtime/ascendc_kernel_unsigned_underflow_invalid_row.md)。


## Evidence

- diff 事实 + 确定性语义（@589b735bc330）：`VFProcessDynamicBlockQuant` 尾块 `Abs`→`Muls/Compare NE/MaskNot/Abs(mask)` 替换逐行对上；「NaN 污染 ReduceMax」为 IEEE 语义 + AscendC 惯用法确定性推断，PR 讨论区仅 /lgtm+/approve 无文字动机。溯源下探 [cann-recipes-infer-pr-433-feat-indexer-compress-epilog-and-kv-compress-epilog-support-hifp8-quant](https://gitcode.com/cann/cann-recipes-infer/merge_requests/433)
- diff 事实（@3f6b03fbfa18）：`custom-npu_lightning_indexer_quant.md`「约束说明」新增「TopK 过程对 NAN 排序是未定义行为」（op-owner 规格声明）；「NaN 破坏稀疏选择」「scale/中间量非法是 NaN 来源」为机制推断、不并入事实面。溯源下探 [cann-recipes-infer-pr-28-feat-add-ascendc-mla-prolog](https://gitcode.com/cann/cann-recipes-infer/merge_requests/28)

<!-- cannbot:related:start -->
## 相关

- [ReduceMax](../../../../ops/ascendc/apis/simd_api/adv_api/reduction_operations/reduce_max_interface/reduce_max.md)（`exemplifies`）：动态 per-block 量化的每块 scale = 块内 `max(｜x｜)`。；对多维向量在指定维度求最大值。定义指定计算维度为R轴（Reduce轴），非指定维度为A轴（Normal轴）。支持指定第一维或最后一维进行reduce。模板参数T支持half/float，pattern指定reduce模式。；API 页补齐 runbook 中块 scale 规约所调用的 ReduceMax 维度与类型合同。
- [AscendC kernel 用无符号整型算有效长度：负差下溢 + Max(x,0) 对无符号是空操作 → 无效 / 短行 aic error](../runtime/ascendc_kernel_unsigned_underflow_invalid_row.md)（`related`）：同类 lightning-indexer / 块量化 kernel 的另一类数值污染——规约 / 排序吃到 NaN/Inf（浮点非有限值，非整型下溢）见 ［precision-nonfinite-nan-inf-quant-indexer-kernel］(../precision/precision_nonfinite_nan_inf_quant_indexer_kernel.md)。；在昇腾 ［AscendC］(../../concepts/frameworks/ascendc.md) 上写 ［Lightning-Indexer］(../../concepts/kernels/lightning_indexer.md) 稀疏选择 / 动态块量化 kernel 时，输出整块变废、稀疏索引不可预期。根因常是 kernel 内的**规约 / 排序算子直接吃到了非有限值 (NaN/Inf)**——IEEE 语义下一个 NaN 就能污染整块规约结果或让排序次序未定义。这类精度问题不 crash、只错值，需在算子内主动剔除非有限值。；焦点明确转介同类 indexer 的浮点污染路径，目标提供规约与排序前的非有限值诊断。
- [Lightning Indexer Kernel](../../concepts/kernels/lightning_indexer.md)（`related`）：“**Top-k 指令实现**：必须是**精确**TopK，不能近似。分三步：”；“量化版 Lightning-Indexer 的 TopK 过程对 NaN 的排序是**未定义行为**（算子规格明载）——NaN 参与排序时相对次序不确定，会使 topk 选出的稀疏 block/token 索引不可预期、破坏稀疏注意力的选择正确性。”。精确 TopK 实现仍需满足非有限值前置条件，目标 runbook给出 NaN 污染的故障信号和约束检查点。
- [QuantLightningIndexer 950 ACLNN 算子知识](../../../../ops/ascendc/operators/aclnn/transformer/attention/quant_lightning_indexer_950.md)（`related`）：- 公开约束要求 `weights*queryScale` 落在 FP16 表示范围；TopK 对 NaN 的排序行为未定义。；量化版 Lightning-Indexer 的 TopK 过程对 NaN 的排序是**未定义行为**（算子规格明载）——NaN 参与排序时相对次序不确定，会使 topk 选出的稀疏 block/token 索引不可预期、破坏稀疏注意力的选择正确性。因此**不要让进入 TopK 的打分矩阵包含 NaN**。相关约束（同规格）：`W ⊙ Scale_Q` 的结果须可被 float16 表示、`query_dequant_scale` / `key_dequant_scale` 须 ≥ 0；违反这些或让反量化中间量出现 inf/NaN，正是把 NaN 引入 topk 输入的来源。。950 算子公开边界声明 TopK 对 NaN 排序未定义，Runbook 给出 NaN/Inf 进入规约或 TopK 后稀疏索引不可预期的症状、mask 探针与 ZEROING 修复，直接推进该数值故障排查。
<!-- cannbot:related:end -->
