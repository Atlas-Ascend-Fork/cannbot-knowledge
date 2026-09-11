---
type: Optimization
title: 视觉编码器 SAM 式分解相对位置偏置：经 pse_shift 融进 npu_prompt_flash_attention 替代 SDPA
description: 昇腾上给带 SAM 式分解相对位置偏置（add_decomposed_rel_pos）的视觉编码器全注意力做提速时，用 torch_npu.npu_prompt_flash_attention（FIA 家族 prefill 全量融合算子）替代 PyTorch SDPA：把分解出的相对位置偏置 rel_h + rel_w 拼成 [B, nHead, S, S]（S = H*W）后经 pse_shift 偏置入参传入，一个算子同时完成 rel-pos bias 叠加 + attention，无需回退 SDPA。调用约定 input_layout="BNSD"、显式给 scale_value（= self.scale）与 num_heads；无相对位置（use_rel_pos=False）时省略 pse_shift 走纯 flash attention 快路径。适用多模态 OCR/VLM 视觉编码器 prefill 阶段（视觉 token 排成 H×W 网格）。参考实现为 vllm-ascend 的 AscendRelPosAttention，经 register_ascend_customop 注册表在 NPU 上替换上游 RelPosAttention。收益仅定性（sdpa->prompt_flash_attention 作为三项加速改动之一，无单项独立数值），验证环境 vLLM 0.19.0 + vllm-ascend、Atlas A2（A2-313T 单机 TP=1）。反例：非分解形式的完整 [S,S] bias 需自构张量；只覆盖 prefill 全量、勿套 decode 因果路径。关键术语：npu_prompt_flash_attention、pse_shift、FIA、BNSD、add_decomposed_rel_pos、SAM 分解 rel-pos、customop 注册表、Atlas A2、vllm-ascend。
tags:
- task.optimization
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/7380
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a2
---

# 视觉编码器 SAM 式分解相对位置偏置：经 pse_shift 融进 npu_prompt_flash_attention 替代 SDPA

## 适用场景

在昇腾上给**带相对位置偏置的视觉编码器注意力**做算子替换提速时适用。命中处境：

- workload 是多模态模型的**视觉编码器 prefill 阶段**（如 OCR / VLM 的 vision tower），视觉 token 排成 `H×W` 网格，注意力在 `S = H*W` 个 token 上做窗口或全局全注意力。
- 该注意力采用 **SAM 式分解相对位置偏置**（`add_decomposed_rel_pos`）：把 2D 相对位置偏置沿 H、W 两个方向分解为 `rel_h`、`rel_w` 两张表，运行时相加得到逐位置的 attention bias，而不是一张完整 `[S, S]` 偏置。上游参考结构见 `RelPosAttention` / `add_decomposed_rel_pos`。
- 现状是该注意力走 **PyTorch SDPA（`scaled_dot_product_attention`）** 路径，未落到昇腾融合 attention 算子，是提速空间所在。

命中后要判断的核心问题：偏置是逐位置的、又想落到昇腾融合 attention 算子，SDPA 之外有没有能同时承载「相对位置 bias + attention」的单算子？有——`torch_npu.npu_prompt_flash_attention` 的 `pse_shift` 偏置入参。

## 条件 → 优先尝试什么

**条件**：视觉编码器全注意力 + SAM 式分解 rel-pos 偏置 + 当前走 SDPA + 目标昇腾提速。

**优先尝试**：用 `torch_npu.npu_prompt_flash_attention` 融合实现替代 SDPA，把分解偏置 `rel_h + rel_w` 拼成 `[B, nHead, S, S]` 后经 **`pse_shift`** 入参传入，一个算子同时完成「rel-pos bias 叠加 + attention」，不必回退到 SDPA。

### 技术要点（通用知识）

- 昇腾融合 attention 算子 `npu_prompt_flash_attention`（FIA 家族的 prefill 全量融合算子，见 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md)）接收一个**逐位置的 attention bias 入参 `pse_shift`**：它在 softmax 前逐元素叠加到打分矩阵上。
- SAM 式相对位置注意力分解出的 `rel_h`、`rel_w` 相加后恰好覆盖 `[B, nHead, S, S]`（此处 `S = H*W`）这张逐位置偏置，语义上正是 `pse_shift` 入参所承载的偏置张量——所以「分解 rel-pos」与「pse_shift 融合」天然契合，无需把偏置退化回 SDPA 的 `attn_mask` 加法路径。
- 无相对位置时（`use_rel_pos=False`）省略 `pse_shift`、直接调用同一算子，走纯 flash attention 快路径；有无偏置共用一个算子调用点，只切换是否带 `pse_shift`。
- 为何有效：把「构造 bias 张量 + 与打分矩阵相加 + softmax + 加权求和」从 SDPA 的多步 eager 计算，收敛成一个融合算子调用，减少中间张量与 kernel 启动，同时保留逐位置偏置的精确语义。

### 调用约定

- `input_layout="BNSD"`，即 `[Batch, Num_heads, Seq=H*W, Head_dim]`；q/k/v 均先 reshape 到该布局。
- 须**显式**给 `scale_value`（= 模型的 `self.scale`，勿依赖算子默认）与 `num_heads`。
- `pse_shift` 形状 `[B, nHead, S, S]`；由 `(rel_h + rel_w)` view 成该形状，`S = H*W`。

## 参考实现及其约束

以下取自 vllm-ascend 对 SAM 类视觉编码器（DeepSeek-OCR-2 deepencoder）的落地，`AscendRelPosAttention(RelPosAttention)` 的 `forward` 关键结构（BNSD）：

```python
B, H, W, _ = x.shape
qkv = self.qkv(x).reshape(B, H*W, 3, self.num_heads, -1).permute(2, 0, 3, 1, 4)
q, k, v = qkv.reshape(3, B*self.num_heads, H*W, -1).unbind(0)
rel_h, rel_w = None, None
if self.use_rel_pos:
    rel_h, rel_w = add_decomposed_rel_pos(q, self.rel_pos_h, self.rel_pos_w, (H, W), (H, W))
q = q.view(B, self.num_heads, H*W, -1)
k = k.view(B, self.num_heads, H*W, -1)
v = v.view(B, self.num_heads, H*W, -1)
if self.use_rel_pos:
    rel_h = rel_h.view(B, self.num_heads, rel_h.size(1), rel_h.size(2), rel_h.size(3))
    rel_w = rel_w.view(B, self.num_heads, rel_w.size(1), rel_w.size(2), rel_w.size(3))
    attn_bias = (rel_h + rel_w).view(B, self.num_heads, rel_h.size(2), rel_h.size(3)*rel_w.size(4))
    x = torch_npu.npu_prompt_flash_attention(
        q, k, v, pse_shift=attn_bias,
        input_layout="BNSD", scale_value=self.scale, num_heads=self.num_heads)
else:
    x = torch_npu.npu_prompt_flash_attention(
        q, k, v, input_layout="BNSD", scale_value=self.scale, num_heads=self.num_heads)
x = x.view(B, self.num_heads, H, W, -1).permute(0, 2, 3, 1, 4).reshape(B, H, W, -1)
x = self.proj(x)
```

挂载方式（该参考实现的工程约束，非技术本身约束）：

- 通过 vllm-ascend 的 customop 注册表在 NPU 上替换上游同名类——`register_ascend_customop` 里把 `"RelPosAttention": AscendRelPosAttention` 注册进 `_ROW`（与 `CustomQwen2Decoder` 同批），从而在昇腾上顶替上游 `RelPosAttention`。迁到别的框架时替换机制需另配，pse_shift 调用约定本身不变。
- `add_decomposed_rel_pos` 的偏置分解语义、`rel_pos_h/rel_pos_w` 两张相对位置表，来自上游 vision 编码器结构（SAM 式），是这一类「分解 rel-pos」的前提；不满足该结构的编码器不适用本规则。

## 依据 / Outcome

- 核心断言（用 `npu_prompt_flash_attention` + `pse_shift` 承载分解 rel-pos 偏置替代 SDPA，及 BNSD / scale_value / num_heads 调用约定）为合并态 diff 事实：`vllm_ascend/ops/rel_pos_attention.py` 全文新增、`utils.py` 注册表新增 `RelPosAttention` 条目。
- 收益仅定性：来源把 `relposattention: sdpa->prompt_flash_attention` 作为三项加速改动之一列出，**未给该项或整体的任何公开复测数值**。捕获源的测试段仅记录验证环境为 vLLM 0.19.0 + vllm-ascend main 与三项优化条目，无吞吐/时延数字。**不外推该替换的单项收益。**

## 反例 / 边界

- 相对位置偏置**不是分解形式**（一张完整 `[S, S]` bias），或不是 SAM 式 `add_decomposed_rel_pos` 结构：仍可考虑经 `pse_shift` 传入，但要自行构造 `[B, nHead, S, S]` 偏置张量，`rel_h + rel_w` 的拼法不再适用。
- 该 diff 只覆盖视觉编码器的 prefill 全量注意力（BNSD、`S = H*W`），未涉及带 KV cache 的增量/因果解码路径；勿把此调用约定直接套到 decode。
- 无 rel-pos 时不要传空 `pse_shift`——走 else 分支省略该入参。

## Evidence

- diff 事实（merge sha `2c4eff51023fd3818d2ecf773b3302841352055b`）：`vllm-project/vllm-ascend@2c4eff5.../vllm_ascend/ops/rel_pos_attention.py`（`AscendRelPosAttention` 全文新增）、`.../vllm_ascend/utils.py`（`register_ascend_customop` 注册 `RelPosAttention`）。调用约定（`pse_shift` / `input_layout="BNSD"` / `scale_value` / `num_heads`）为 diff 原文。
- 溯源下探：[vllm-ascend-pr-7380-optimize-deepseekocr2-relposattention-and-customqwen2decoder-and-add-doc](https://github.com/vllm-project/vllm-ascend/pull/7380)

## Links

- [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md) — `npu_prompt_flash_attention` 属 FIA 家族的 prefill 全量融合算子；本页的 `pse_shift` 偏置入参、BNSD 布局、`scale_value`/`num_heads` 调用约定同源于该算子族。
- [mm-encoder-packed-attention-seqlen-semantics](../../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md) — 同类模式：昇腾多模态编码器把原生 / SDPA 注意力替换为 npu fusion attention 算子；那页讲 packed 全注意力两个可互换融合算子的 seq_len 语义差异，与本页互为参照。