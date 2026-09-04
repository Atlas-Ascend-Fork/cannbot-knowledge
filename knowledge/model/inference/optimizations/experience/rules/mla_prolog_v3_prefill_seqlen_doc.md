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

<!-- cannbot:related:start -->
## 相关

- [MLA-prolog + zigzag-CP Prefill 必须用两段式 KV cache 写（勿按 slot_mapping 直写 paged cache）](mla_prolog_zigzag_cp_kv_write.md)（`related`）：“「共用同一算子」指调用入口相同，**不代表 prefill / decode 的调用参数相同**：二者按阶段分别组装入参。尤其 CP prefill 下 paged KV cache 的写法有额外正确性要求（临时 BSND cache + all-gather + zigzag 逆序回写，勿按 slot_mapping 直写），见 ［mla-prolog-zigzag-cp-kv-write］(mla_prolog_zigzag_cp_kv_write.md)。”与“结构为 ［mla-prolog］(../../../concepts/kernels/mla_prolog.md)（算子 `torch.ops.custom.npu_mla_prolog_v3`）+ paged KV cache（［kv-cache-manager］(../../../concepts/frameworks/kv_cache_manager.md)）的 **Prefill**，且叠加了 ［zigzag-cp］(../../../concepts/parallelism/zigzag_cp.md)（CP 仅在 prefill 生效，与长上下文 `input_max_len` 16384/32768 搭配）时：**不能**让 prolog 算子按 `slot_mapping` 直写最终 paged cache，必须改成两段式 KV 写。覆盖 `kv_cache_quant_mode ∈ {int8(C8), 非量化}`，证据来自 ［deepseek-v3.2-exp］(../../../concepts/models/deepseek_v3_2_exp.md)。这是把 ［long-seq-prefill-context-parallel］(long_seq_prefill_context_parallel.md) 落到 MLA-prolog 上时的一处必配正确性细节。”分别限定调用入口与 KV 写回方式。前者确认 prolog 可用于长序列 prefill 并指出 CP 参数分支，后者给出该 CP 分支的临时 BSND、all-gather、逆序和 paged-cache 回写合同。
<!-- cannbot:related:end -->
