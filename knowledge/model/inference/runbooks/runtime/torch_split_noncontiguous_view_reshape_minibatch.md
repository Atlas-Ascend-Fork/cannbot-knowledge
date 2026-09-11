---
type: Runbook
title: torch.split / 切片产出的非连续张量做展平：用 .reshape 而非 .view（bsz>1 才暴露，单批自测会掩盖）
description: torch.split / 切片产出的非连续张量做展平：用 .reshape 而非 .view（bsz>1 才暴露，单批自测会掩盖）。在昇腾上跑 PyTorch 建模代码，某段在 batch size（minibatch）> 1 时对张量做展平报 view 相关错误（要求内存连续、无法 view）；bsz==1 时完全正常。观测于 context-parallel prefill 分支里对 all-gather + 重排后按 dim=1 split 出的半张量做展平的路径。
tags:
- task.debugging
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/59
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# torch.split / 切片产出的非连续张量做展平：用 .reshape 而非 .view（bsz>1 才暴露，单批自测会掩盖）

## 信号（现象）

在昇腾上跑 PyTorch 建模代码，某段在 batch size（minibatch）> 1 时对张量做展平报 view 相关错误（要求内存连续、无法 view）；bsz==1 时完全正常。观测于 [context-parallel](../../concepts/parallelism/context_parallel.md) prefill 分支里对 all-gather + 重排后按 `dim=1` split 出的半张量做展平的路径。

## 触发条件

- 对 `torch.split(x, ..., dim=1)` / 高维切片产出的**可能非连续**张量调用 `.view(-1, ...)` 展平。
- bsz > 1：同一半张量内不同 batch 的行之间隔着另一半的元素、stride 不连续。bsz == 1 时前 / 后缀切片各自恰好连续，`.view` 不报错、问题被掩盖。

## 根因

`torch.split(x, x.size(1)//2, dim=1)` 沿非最内维切出的两半是原张量的**非连续视图**。`.view` 要求展平维在内存中连续，跨越非连续子空间即失败。bsz==1 时切片连续所以 view 侥幸通过，掩盖了 minibatch bug。

## 修法

把这类展平从 `.view` 改为 `.reshape`：

```python
# CP prefill 分支：沿 dim=1 split 出 prev/next 两半后展平
prev, next = torch.split(x, x.size(1) // 2, dim=1)
- prev = prev.view(-1, prev.shape[-1])
- next = next.view(-1, next.shape[-1])
+ prev = prev.reshape(-1, prev.shape[-1])
+ next = next.reshape(-1, next.shape[-1])
```

`.reshape` 在张量非连续时自动 copy 成连续再变形、连续时等价 view，因此对「可能非连续」的 split / 切片产物是安全选择。

## 可迁移原则

- 对 `torch.split` / 转置 / 高维切片等**可能产出非连续张量**的结果做展平（`view(-1, ...)`），一律用 `.reshape`——除非能确证该张量连续。`.view` 只在确定连续时用。
- 这类 bug 只在 bsz > 1 暴露：**建模代码的正确性自测必须覆盖 minibatch > 1**，只按单 batch 跑通不能证明 split / reshape 路径正确。

## 参考实现及其约束

参考实现在 cann-recipes-infer DeepSeek-V3.2-Exp（[DSA](../../concepts/modules/dsa.md)）的 [lightning indexer](../../concepts/kernels/lightning_indexer.md) `Indexer.forward` 的 context-parallel prefill 分支（`cp_size > 1 and is_prefill`）：该分支 all-gather 后按 `cp_reverse_index` 重排、沿 `dim=1` split 成 prev/next（load-balanced / [zigzag-CP](../../concepts/parallelism/zigzag_cp.md) 双 chunk 重构），涉及 C8 KV cache 路径的 `query_dequant_scale_prev/next` 与通用路径的 `weights_prev/next` 共 4 处 `.view`→`.reshape`。此约束是 PyTorch view/reshape 连续性语义的通用面，不限该模型。

## 相关经验

- MLA-Prolog + zigzag-CP prefill 的两段式 KV cache 写（同为 CP prefill 分支的正确性坑）见 [mla-prolog-zigzag-cp-kv-write](../../optimizations/experience/rules/mla_prolog_zigzag_cp_kv_write.md)。
- 长序列 prefill 优先 context parallel 的整体取向见 [long-seq-prefill-context-parallel](../../optimizations/experience/rules/long_seq_prefill_context_parallel.md)。

## Evidence

- `diff 事实`（@ef0f82d0）：`indexer.py` 的 `Indexer.forward` `if self.cp_size > 1 and is_prefill:` 分支内 4 处 `.view(-1, ...)`→`.reshape(-1, ...)`（`query_dequant_scale_prev/next` 在 `if self.kv_cache_c8` 内、`weights_prev/next` 在通用分支）逐行对上，张量来自 `torch.split(..., dim=1)`。「非连续 + bsz>1 → view 失败」为 PyTorch view/reshape 连续性语义 + split(dim=1) 布局推断，与 PR 标题「minibatch>1 bug」一致；无独立复测。溯源下探：[cann-recipes-infer-pr-59-fix-fix-minibatch-1-bug-and-remove-redundent-code](https://gitcode.com/cann/cann-recipes-infer/merge_requests/59)