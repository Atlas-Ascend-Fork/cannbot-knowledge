---
type: Runbook
title: 量化特性所需状态被误挂在无关并行分支（CP 度）里 → 跳过该分支的配置静默丢状态（SFA C8 prefill 单卡漏填 per-token scale）
description: 某个量化配置只在单卡挂 / 只在某并行度挂：开了量化特性且并行度取某个值（如 cp_size=1，无 context-parallel）时报错，换更高并行度（cp_size>1）就不复现。 具体观测实例：deepseek-v3.2-exp 走 mla-prolog + sparse-flash-attention（SFA）路径，开 C8 家族的 SFA C8 KV-cache 量化（kv_cache_c8=True）且 cp_size=1 时，prefill 路径报错、decode 路径正常——症状只在"单卡 + C8 + prefill"三条件同时成立时出现（源未披露具体错误文本）。
tags:
- task.debugging
- topic.attention
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/76
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 量化特性所需状态被误挂在无关并行分支（CP 度）里 → 跳过该分支的配置静默丢状态（SFA C8 prefill 单卡漏填 per-token scale）

## 信号（症状，供对号入座）

- 某个**量化配置只在单卡挂 / 只在某并行度挂**：开了量化特性且并行度取某个值（如 `cp_size=1`，无 [context-parallel](../../concepts/parallelism/context_parallel.md)）时报错，换更高并行度（`cp_size>1`）就不复现。
- 具体观测实例：[deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md) 走 [mla-prolog](../../concepts/kernels/mla_prolog.md) + [sparse-flash-attention](../../concepts/kernels/sparse_flash_attention.md)（SFA）路径，开 [C8](../../concepts/quantization/w8a8c8.md) 家族的 SFA C8 KV-cache 量化（`kv_cache_c8=True`）**且** `cp_size=1` 时，**prefill 路径报错、decode 路径正常**——症状只在"单卡 + C8 + prefill"三条件同时成立时出现（源未披露具体错误文本）。

## 触发条件

开某量化特性（`kv_cache_c8=True`）+ 该特性所需的状态填充语句恰好被写在某并行分支（`if cp_size > 1:`）内 + 实际并行度使该分支被跳过（`cp_size=1`）。

## 根因 = 失败签名

**特性 X 必需的状态赋值，被误挂在与 X 无关的条件分支（此处是 CP 度）里；跳过该分支的配置就静默丢掉该状态。**

具体：下游 C8 注意力需要 per-token 反量化 scale `c8_input_dict['pertoken_scale']`（取自 MLA-Prolog 算子 `npu_mla_prolog_v3` 的第 5 个返回 `dequant_q_norm`）。该键的填充语句被写在 `if cp_size > 1:` 块内的 C8 子分支里：

```python
if self.cp_size > 1:
    ...
    if self.kv_cache_c8:
        c8_input_dict.update({'pertoken_scale': dequant_q_norm})   # 只在 cp_size>1 时执行
```

当 `cp_size=1` 时整个 `if cp_size > 1:` 块被跳过，`pertoken_scale` 永不写入，下游 C8 注意力拿不到 scale 而报错。

**判据线索（不对称即是 tell）**：decode 路径本就把同一句放在 CP 分支之外、仅由 `if kv_cache_c8:` 守卫，因此 bug 只活在 prefill 一侧。遇到"某量化配置只在单卡挂 / 只在某并行度挂"的怪异条件依赖时，**先 diff prefill 与 decode 两条路径找不对称点**。

## 修法与可迁移通则

- **修法**：把 `pertoken_scale` 填充从 CP 分支中移出，改由量化开关独立守卫（`if kv_cache_c8:`，与 `cp_size` 无关），使 prefill 与 decode 对齐——只要开 C8 KV cache 就一定填 scale。
- **可迁移通则**：凡"特性 X 必需的状态赋值"落在与 X 无关的条件分支里，跳过该分支的配置就会静默丢状态。**量化 / 特性所需状态应由该特性自己的开关守卫，不由并行度等无关维度守卫**；改动任一注意力路径的量化分支后，务必对拍 prefill vs decode 的守卫条件是否对称。

## 相关

- MLA-Prolog + CP 的 prefill KV cache 写入两段式（另一处 prefill/decode 路径差异易踩的坑）见 [mla-prolog-zigzag-cp-kv-write](../../optimizations/experience/rules/mla_prolog_zigzag_cp_kv_write.md)。
- C8 KVCache 与 PyPTO Lightning Indexer 的互斥约束见 [c8-kvcache-disables-pypto-lightning-indexer](../../optimizations/experience/anti_patterns/c8_kvcache_disables_pypto_lightning_indexer.md)。
- 范围：限定 cann-recipes-infer 本仓 DeepSeek-V3.2-Exp 建模文件 `mlaprolog_prefill`，及可迁移到同类"量化状态被误挂 CP / 并行分支"的失败签名；不外推到整个昇腾栈。

## Evidence

- **diff 事实**（clone `@8bf2846517723eff`）：读到实际 merged diff 与同 sha 原文件 `mlaprolog_prefill` / `mlaprolog_decode` 上下文，确认被删句原在 `if cp_size > 1:` 块内、decode 侧本就仅由 C8 守卫——佐证 bug 仅存于 prefill。核心断言（scale 填充被误挂 CP 分支、单卡跳过、修法为按 C8 开关守卫）为 diff 事实；具体报错文本源未披露，如实标注不编造。
- 溯源下探：[cann-recipes-infer-pr-76-fix-sfa-c8-cp-size-1-bugfix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/76)
