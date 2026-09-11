---
type: Optimization
title: 块内双向注意力（掩码扩散 / DLLM 解码）走 FIA 非因果全注意力，勿套 causal FA 快路径
description: 块内双向注意力（掩码扩散 / DLLM 解码）走 FIA 非因果全注意力，勿套 causal FA 快路径。在昇腾上适配一类块内注意力是双向的模型（Diffusion LLM / DLLM，掩码扩散式解码——一个块内并行逐步去掩码，块内所有位置互相可见），而不是自回归 causal 时。这类模型若沿用平台通用 causal FA 快路径，结果会错：causal 只算下三角、丢掉上三角，而块内是全连接语义。典型症状是解码输出异常但无报错（算子接受了非因果 shape、只是语义不对）。
tags:
- task.optimization
- topic.attention
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/284
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# 块内双向注意力（掩码扩散 / DLLM 解码）走 FIA 非因果全注意力，勿套 causal FA 快路径

## 适用场景（问题信号）

在昇腾上适配一类**块内注意力是双向的**模型（Diffusion LLM / DLLM，掩码扩散式解码——一个块内并行逐步去掩码，块内所有位置互相可见），而不是自回归 causal 时。这类模型若沿用平台**通用 causal FA 快路径**，结果会错：causal 只算下三角、丢掉上三角，而块内是全连接语义。典型症状是解码输出异常但无报错（算子接受了非因果 shape、只是语义不对）。

## 规则 / 优先怎么做

1. **不要走通用 causal FA 快路径** `torch_npu._npu_flash_attention_qlens`。它的进入判据是 `qk_head_dim<=128 and causal`——语义只覆盖 causal，块内双向不符，套上去等于强行按下三角算。
2. **把双向注意力改路由到 [FIA](../../../concepts/kernels/fused_infer_attention_score.md) 的「全（非因果）注意力」路径**：核心开关是 `atten_mask=None`（无 causal mask → 块内全连接）。先把 K/V 写入 paged kv-pool，再以 `atten_mask=None` + `input_layout="TND"` + `block_size=page_size` 做全注意力：

   ```python
   torch.ops.npu.npu_fused_infer_attention_score(
       query, k_cache, v_cache,
       block_table=...,
       block_size=page_size,          # KV 分块粒度 = page_size
       num_heads=..., num_key_value_heads=...,
       input_layout="TND",
       atten_mask=None,               # 全注意力，无 causal mask —— 双向语义的关键
       scale=..., actual_seq_lengths=..., actual_seq_lengths_kv=...,
   )
   ```

3. **用一个 DLLM 标志门控关闭 causal 快路径**，而不是全局改判据：在快路径进入判据后追加 `and not <is_dllm_model>`，双向模型不进 `_npu_flash_attention_qlens`、改由前置分流走上面的全注意力入口。这样自回归模型的 causal 快路径不受影响。

## 为什么有效

- causal FA 只计算下三角（每个位置只看自己及更早位置）。DLLM 一个块内所有位置互相可见（双向），套 causal 会漏算上三角、结果错。
- FIA 传 `atten_mask=None` 才得到块内全连接语义——这是把「非因果 / 双向」需求落到融合算子的正确开关，`input_layout="TND"` + `block_size=page_size` 承接 paged KV 的变长与分块。

## 参考实现及其约束

- 参考实现：cann-recipes-infer 的 LLaDA2.x-sglang 昇腾适配。框架为 sglang `AscendAttnBackend`（`--attention-backend ascend`、`--device npu`），paged KV。
- 该实现用 `is_dllm_model` 标志（由 `DllmConfig.from_server_args` 非空触发）门控关闭 causal 快路径，并把 `forward` 前置分流到 `forward_dllm`（其内即上面的 `atten_mask=None` 全注意力调用）。
- 迁移到其它块内双向注意力模型时，可复用的核心是「**双向 / 非因果注意力必须绕开只覆盖 causal 的快路径，改走无 mask 的全注意力算子**」；门控标志名、分流入口、config 触发条件随各自框架实现而变，不是技术本身的门槛。

## 反例 / 边界

- **别一刀切到自回归模型**：自回归 causal decode 应保留 causal 快路径 / causal sparse_mode，套 `atten_mask=None` 反而丢因果约束、且慢。这条规则只适用于**块内双向**的注意力段。
- 规则适用面限「块内双向注意力 + 昇腾 sglang FIA」证据覆盖场景，不外推到 causal 模型或其它框架栈。

## 相关经验
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpa](../../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md)

- causal / attention-sink / 滑窗等**因果变体**如何用 `sparse_mode` 映射到 FIA，见 [attention-to-fia-sparse-mode-sink-window](attention_to_fia_sparse_mode_sink_window.md)（本页是其「非因果 / 双向」的对偶：那里选 causal 系列 sparse_mode，这里选 `atten_mask=None` 全注意力）。
- FIA 的 `actual_seq_lengths_kv` 变长实参类型随后端不同，见 [fia-actual-seq-lengths-kv-backend-type](../../../runbooks/runtime/fia_actual_seq_lengths_kv_backend_type.md)。
- FIA 承接 paged KV cache 的读写约定，见 [ascend-paged-attention-kv-cache](ascend_paged_attention_kv_cache.md)。

## Evidence

- `diff 事实`（clone `@8cd85a87af03`）：patch 0001/0002——快路径进入判据加 `and not self.is_dllm_model`（0001 加、0002 改由 `forward` 前置分流到 `forward_dllm`）；`forward_dllm` 内 `npu_fused_infer_attention_score` 参数为 `atten_mask=None`、`input_layout="TND"`、`block_size=self.page_size`。归因主语为本仓 LLaDA2.x-sglang 昇腾适配。
- 溯源下探：[cann-recipes-infer-pr-284-feat-llada2-x-sglang-ascend](https://gitcode.com/cann/cann-recipes-infer/merge_requests/284)