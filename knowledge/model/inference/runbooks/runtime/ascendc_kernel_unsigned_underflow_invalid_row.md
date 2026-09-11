---
type: Runbook
title: AscendC kernel 用无符号整型算有效长度：负差下溢 + Max(x,0) 对无符号是空操作 → 无效 / 短行 aic error
description: AscendC kernel 用无符号整型算有效长度：负差下溢 + Max(x,0) 对无符号是空操作 → 无效 / 短行 aic error。昇腾 AscendC 自定义算子（观测于 lightning_indexer / lightning_indexer_quant 的 preload kernel）在某些「行无效 / 短行」场景触发 aic error（AI Core 报错）——不是所有 shape 都错，只在有效 S1 长度大于有效 S2 长度（本该为负的长度差）的行上崩。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/137
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# AscendC kernel 用无符号整型算有效长度：负差下溢 + Max(x,0) 对无符号是空操作 → 无效 / 短行 aic error

## 信号（现象）

昇腾 [AscendC](../../concepts/frameworks/ascendc.md) 自定义算子（观测于 [lightning_indexer](../../concepts/kernels/lightning_indexer.md) / `lightning_indexer_quant` 的 preload kernel）在某些「行无效 / 短行」场景触发 aic error（AI Core 报错）——不是所有 shape 都错，只在有效 S1 长度大于有效 S2 长度（本该为负的长度差）的行上崩。

## 触发条件

- kernel 里用无符号整型（`uint32_t`）计算「有效长度差」，如 `validS2LenBase = actS2Size - actS1Size`，且下游据此算需处理的基础块数 `(validS2Len + s2BaseSize - 1) / s2BaseSize`。
- 运行时出现 `actS1Size > actS2Size`（有效 S1 长度大于有效 S2 长度）的行。

## 根因

两处无符号语义陷阱叠加：

1. **无符号减法下溢**：`actS2Size - actS1Size` 在 `actS1Size > actS2Size` 时对 `uint32_t` 下溢为接近 2^32 的巨值，符号信息丢失，后续长度计算全乱。
2. **`Max(x, 0)` 对无符号量是空操作**：本意用 `validS2Len = Max(validS2Len, 0)` 兜住下限，但对 `uint32_t` 恒 `≥ 0`，该保护形同虚设，未能把某行的 `validS2Len` 抬到期望下限；返回块数可能落到 0（无效行）。

下游按 0 块 / 下溢巨值处理该行 → AI Core 报错。（「0 块 → aic error」的具体因果为据 kernel 上下文推断；PR 自述与维护者审批仅确认「invalid row 场景 aic error」症状，未给复现数据。）

## 修法

把相关中间量由 `uint32_t` 改为 `int32_t` 有符号运算，并把下限从 `Max(x, 0)` 抬到真正有效的 `Max(x, 1)`：

```cpp
- uint32_t validS2LenBase = actS2Size - actS1Size;
- uint32_t validS2Len = s1Offset + validS2LenBase + constInfo.s1BaseSize;
- validS2Len = Min(validS2Len, actS2Size);
- validS2Len = Max(validS2Len, 0);
+ int32_t validS2LenBase = static_cast<int32_t>(actS2Size) - static_cast<int32_t>(actS1Size);
+ int32_t validS2Len = s1Offset + validS2LenBase + constInfo.s1BaseSize;
+ validS2Len = Min(validS2Len, static_cast<int32_t>(actS2Size));
+ validS2Len = Max(validS2Len, 1);
  return (validS2Len + constInfo.s2BaseSize - 1) / constInfo.s2BaseSize;
```

要点：显式 `static_cast<int32_t>` 后减法可为负、不再下溢；`Max(., 1)` 在有符号下真正生效，保证每行至少 1 块、不再出现 0 块的无效行。

## 可迁移原则

- kernel 里凡是「两个长度 / 下标相减」且差值理论上可为负的表达式，别用无符号类型——无符号下溢会把负值变成巨正值，且后续所有 `Max(x, 0)` 式的下限保护对无符号量全部失效。用有符号 `int32` 并把下限抬到业务上真正的最小值（如块数 ≥ 1）。
- 这类 bug 只在特定 shape（有效 S1 > 有效 S2 的行）暴露，标定 shape 的自测常测不到；验证要覆盖「短行 / 长度差为负」的边界场景。

## 参考实现及其约束

参考 cann-recipes-infer 的 `lightning_indexer` 与 `lightning_indexer_quant` 两个 preload kernel 的 `GetS2BaseBlockNumOnMask`（两文件逻辑相同、同步修改，各 +4/-4）。范围限这两个算子该函数的语义，不外推整栈；观测于 [DSA](../../concepts/modules/dsa.md) 系算子；「0 块 → aic error」为据代码推断、非独立复测。

## 相关经验

- 同类 lightning-indexer / 块量化 kernel 的另一类数值污染——规约 / 排序吃到 NaN/Inf（浮点非有限值，非整型下溢）见 [precision-nonfinite-nan-inf-quant-indexer-kernel](../precision/precision_nonfinite_nan_inf_quant_indexer_kernel.md)。
- 稀疏 attention kernel 的变长 / 零长度边界 golden 见 [precision-sparse-attention-kernel-boundary-golden](../precision/precision_sparse_attention_kernel_boundary_golden.md)。

## Evidence

- `diff 事实`（@91706c75）：`LIPreload::GetS2BaseBlockNumOnMask`（`lightning_indexer_kernel.h`）与 `LIQPreload::GetS2BaseBlockNumOnMask`（`lightning_indexer_quant_kernel.h`）均 +4/-4，`uint32_t`→`int32_t`（含对 `actS2Size`/`actS1Size` 的 `static_cast<int32_t>`）+ `Max(.,0)`→`Max(.,1)` 逐行对上。「invalid row aic error」为 PR 自述 + 维护者审批；「0 块 → aic error」因果为据代码推断、未并入事实面、无独立复测。溯源下探：[cann-recipes-infer-pr-137-fix-fix-invalid-row-scenario](https://gitcode.com/cann/cann-recipes-infer/merge_requests/137)