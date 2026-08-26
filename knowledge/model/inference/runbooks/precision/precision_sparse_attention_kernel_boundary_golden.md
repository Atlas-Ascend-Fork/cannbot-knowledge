---
type: Runbook
title: 稀疏 attention (SFA / SFAA / Lightning-Indexer) 的变长零长度边界与 CPU 真值校验精度陷阱
description: 稀疏 attention (SFA / SFAA / Lightning-Indexer) 的变长零长度边界与 CPU 真值校验精度陷阱。在昇腾上写 / 调试 稀疏 flash attention / Lightning-Indexer（DSA 稀疏注意力）类 AscendC 算子时，出现「变长 batch 里某些形状精度失败、退化形状下又测不出来」的问题。这类精度 bug 集中在两处：kernel 内部的变长 / 零长度 (KV 长度为 0) 边界处理，以及CPU 真值 (golden) 校验脚本的布局与用例设计。
tags:
- task.debugging
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/40
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/148
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/161
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 稀疏 attention (SFA / SFAA / Lightning-Indexer) 的变长零长度边界与 CPU 真值校验精度陷阱

## 适用场景

在昇腾上写 / 调试 [稀疏 flash attention](../../concepts/modules/sparse_flash_attention.md) / [Lightning-Indexer](../../concepts/kernels/lightning_indexer.md)（[DSA](../../concepts/modules/dsa.md) 稀疏注意力）类 [AscendC](../../concepts/frameworks/ascendc.md) 算子时，出现「变长 batch 里某些形状精度失败、退化形状下又测不出来」的问题。这类精度 bug 集中在两处：**kernel 内部的变长 / 零长度 (KV 长度为 0) 边界处理**，以及**CPU 真值 (golden) 校验脚本的布局与用例设计**。

## 陷阱 1：变长 batch 中 KV 长度为 0 未短路 → phantom block 精度失败

变长 batch 里某条序列实际 KV 长度（`actS2Size`）为 0 时，计算掩码下 S2 base block 数量的函数若不短路，负算术（`validS2LenBase = 0 - actS1Size` 为负）会算出非零 / 错误块数，使 preload 处理并不存在的 KV 数据→精度失败。修法是入口早退：

```cpp
uint32_t GetS2BaseBlockNumOnMask(uint32_t s1gIdx, uint32_t actS1Size, uint32_t actS2Size) {
    if (actS2Size == 0) { return 0; }   // 变长/零长度短路守卫
    ...
}
```

fp 与量化两个 kernel 变体（`lightning_indexer` / `lightning_indexer_quant`）都要加同一守卫。

## 陷阱 2：kernel 内「实际有效处理长度」不要各函数本地重算

同一 kernel 里「当前 tile 实际有效的内层处理长度」应由**唯一预算字段**（如 `actualSingleProcessSInnerSize`）统一供给。若某些函数用 `s2Idx*s2BaseSize` / `actS2Size` tiling 公式**本地重算** `s2ProcessSize`，会与规范字段分叉——在稀疏块大小 `sparseBlockSize != 1` 或 `curlen==0`（规范值为 0 而本地公式给非 0）时，喂给稀疏配对 / 掩码 / KV 合并边界的 `s2Pair` / `s2Mid` / `s2GmLimit` 算错→精度失败。修法：改用规范字段。

```cpp
// 本地重算（错）：s2ProcessSize = s2Idx*s2BaseSize + ... > actS2Size ? actS2Size - ... : s2BaseSize
int64_t s2ProcessSize = info.actualSingleProcessSInnerSize;   // 改用 kernel 全局的 0 值保护字段
```

一般原则：kernel 的零值 / 边界保护若由某个规范字段统一把关，所有派生量都从它取，别在各函数里凭 tiling 参数各算一份。

## 陷阱 3：CPU 真值校验——辅助张量要随 q/k/v 同步转置，且勿用退化形状

为稀疏 / 分块注意力写 CPU golden 时，凡随 q/k/v 一起做布局转置（BSND↔BNSD）的辅助张量都要**一并转置、保持轴序一致**。曾出现真值把 q/k/v 转成 BNSD、却漏了对 `sparse_indices` 同构转置，随后按 BNSD 顺序 `[batch, n2_idx, s1_idx, :]` 索引仍是 BSND 的 `sparse_indices`，S 与 N 维错位、取到错误稀疏块索引：

```python
q_bnsd = np.transpose(..., axes=(0, 2, 1, 3))
sparse_indices = np.transpose(sparse_indices, axes=(0, 2, 1, 3))   # 遗漏这行 → S/N 错位
```

更隐蔽的是**用例用退化形状掩盖 bug**：`act_seq_q=[1]*B` 使 query 维恒为 1、稀疏索引 S/N 两轴均为 1，`[b,n2,s1,:]` 与 `[b,s1,n2,:]` 取到同一元素，布局错位被完全掩盖。校验用例必须用真实 per-batch 序列长度（`act_seq_q=[S]*B, act_seq_kv=[SKV]*B`），并覆盖非退化形状（含 TND + PA_BSND 等），才能暴露 S/N 轴错位这类布局 bug。

## 参考实现及其约束

- 陷阱 1 参考实现：cann-recipes-infer 的 `lightning_indexer` / `lightning_indexer_quant` op_kernel（`GetS2BaseBlockNumOnMask`）。
- 陷阱 2 参考实现：`sparse_flash_attention_antiquant` 的 MLA 向量算子（`ElewiseCompute` / `MergeKv` 的 `s2ProcessSize`），触发条件 `sparseBlockSize != 1` / `curlen==0`。
- 陷阱 3 参考实现：`ops/ascendc/examples/test_npu_sparse_flash_attention.py` 的 `cpu_sparse_flash_attention`（DSA / DeepSeek 稀疏注意力真值）。
- 边界：这些函数名 / 字段名是各参考实现的具体形态；「零长度短路 / 规范字段统一供给 / 辅助张量同步转置 + 非退化测试形状」的原则适用于稀疏、分块注意力算子及其校验，不外推为整栈通用律。

## Evidence

- diff 事实（@3253316）：两处 kernel `GetS2BaseBlockNumOnMask` 各加 `actS2Size==0` 早退；phantom block 内部机制为读上下文推断。溯源下探 [cann-recipes-infer-pr-161-fix-fix-precisionfail-when-acts2-0](https://gitcode.com/cann/cann-recipes-infer/merge_requests/161)
- diff 事实（@04f9edd83104，+2 −6 单文件）：`s2ProcessSize` 本地重算 → 改用 `actualSingleProcessSInnerSize`；`curlen==0` 触发链为对 diff + 上下文的机制推断。溯源下探 [cann-recipes-infer-pr-148-fix-fix-precisionfail-in-curlen-equal-0](https://gitcode.com/cann/cann-recipes-infer/merge_requests/148)
- diff 事实 + 维护者确认（buggy 父 @8dd3a3b / 修复 @918b806）：真值新增 `sparse_indices` 转置 + 用例改真实 per-batch 长度 + 新增 TND/PA_BSND 用例；reporter 复核真值修改无误。溯源下探 [cann-recipes-infer-issue-40-bug-report-sparsefa-cpu-sparse-flash-attention-sparse-indices](https://gitcode.com/cann/cann-recipes-infer/issues/40)
