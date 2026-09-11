---
type: Optimization
title: MLA 前处理超级融合算子可用于长序列 Prefill — 勿被算子文档 Seq-Length 0~16 标注误导
description: 给 MLA 类模型（mla，如 deepseek-v3.2-exp / LongCat-Flash / Kimi-K2-Thinking）在昇腾 NPU 上搭 attention 前处理（Q/KV 投影 + RMSNorm + RoPE + KV Cache 写入）融合路径时，Prefill 与 Decode 应共用同一个超级融合前处理算子 npu_mla_prolog_v3——不要因为看到该算子文档标「Seq-Length 取值范围 0~16」就把它排除出 prefill、退回分步小算子。该算子实际支持的 Seq-Length 是 1–65536，可覆盖长序列 prefill。
tags:
- task.optimization
- topic.attention
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/89
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MLA 前处理超级融合算子可用于长序列 Prefill — 勿被算子文档 Seq-Length 0~16 标注误导

## 条件 → 优先怎么做

给 MLA 类模型（[mla](../../../concepts/modules/mla.md)，如 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) / LongCat-Flash / Kimi-K2-Thinking）在昇腾 NPU 上搭 attention 前处理（Q/KV 投影 + RMSNorm + RoPE + KV Cache 写入）融合路径时，**Prefill 与 Decode 应共用同一个超级融合前处理算子 [npu_mla_prolog_v3](../../../concepts/kernels/mla_prolog.md)**——不要因为看到该算子文档标「Seq-Length 取值范围 0~16」就把它排除出 prefill、退回分步小算子。该算子实际支持的 Seq-Length 是 **1–65536**，可覆盖长序列 prefill。

## 问题信号（会误导 agent 的坑）

`npu_mla_prolog_v3`（beta / op-plugin）把 MLA 前处理的四条并行计算路径融成一次调用，是相对分步 `npu_kv_rmsnorm_rope_cache_v2` 的「超级融合」形态。其某版本算子文档把「Seq-Length（输入样本序列长度）取值范围」标注为 **0~16**。优化 agent 若按字面理解，会误判该算子只能处理极短序列 → 认为它**只能用于 decode、不能用于 prefill** → 在 prefill 侧规避它、退回小算子拼接或另找方案。这是**文档低估算子能力**造成的误判，不是算子的真实边界。

## 依据

- **维护者确认**：`npu_mla_prolog_v3` 当前 Seq-Length 实际支持范围是 **1–65536**，可应用于 prefill；文档标注的 0~16 并非真实上限。这是「1–65536」这一具体数字的唯一来源（未独立读到 op-plugin 算子规格文档做二次核对）。
- **参考实现印证「确用于 prefill」**（cann-recipes-infer 的 [deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) 建模文件）：
  - `modeling_deepseek.py` 有专门的 `mlaprolog_prefill(...)` 函数，内部调用 `torch_npu.npu_mla_prolog_v3(...)`，与 decode 路径的调用并列；参数按 prefill/decode 分别组装（如 CP 使能时 prefill 走 `cp_tmp_kv_cache_nope/rope` + `mla_prolog_slot_mapping`）。
  - fusion 参考文档注明：`# ─── 超级融合 prolog（Prefill 和 Decode 都用 npu_mla_prolog_v3）───`。

## 反例 / 边界

- 1–65536 上限来自维护者披露、未独立复核；不外推为「任意 MLA 变体 / 任意 head_dim 都是这个范围」，也不写 prefill 下的性能数字（源未给）。
- 「共用同一算子」指调用入口相同，**不代表 prefill / decode 的调用参数相同**：二者按阶段分别组装入参。尤其 CP prefill 下 paged KV cache 的写法有额外正确性要求（临时 BSND cache + all-gather + zigzag 逆序回写，勿按 slot_mapping 直写），见 [mla-prolog-zigzag-cp-kv-write](mla_prolog_zigzag_cp_kv_write.md)。
- 本经验的判断点是「算子能不能用于长序列 prefill」，与「长序列 prefill 该用什么并行」正交——后者见 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md)。

## Evidence

- **维护者确认**：Seq-Length 实际支持 1–65536、可用于 prefill（文档标注的 0~16 非真实上限）。
- **diff 事实**（clone `@2c45117`）：`models/deepseek-v3.2-exp/models/modeling_deepseek.py` 存在函数 `mlaprolog_prefill` 且其中调用 `torch_npu.npu_mla_prolog_v3`；`.agents/skills/model-infer-fusion/references/module-attention-mla-indexer.md` 注明「Prefill 和 Decode 都用 npu_mla_prolog_v3」。二者独立印证「该算子确用于 prefill」。
- 溯源下探：[cann-recipes-infer-issue-89-question-npu-mla-prolog-v3-prefill](https://gitcode.com/cann/cann-recipes-infer/issues/89)