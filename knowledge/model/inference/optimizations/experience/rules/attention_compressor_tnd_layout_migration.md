---
type: Optimization
title: 把注意力/compressor 算子迁到 TND packed-sequence 的调用约定（合轴 query、actual_seq_qlen、dequant_scale 同轴、按阶段切布局）
description: 把注意力/compressor 算子迁到 TND packed-sequence 的调用约定（合轴 query、actual_seq_qlen、dequant_scale 同轴、按阶段切布局）。当仓/框架把注意力布局统一到 TND（token 打平的 packed-sequence）后，需要把某个仍走 BSND/BSH 的注意力或 KV 压缩算子迁上来。迁移不是改个 layout 字符串——有一组必须同步改的调用约定，漏一处就 shape 报错或数值错位。
tags:
- task.optimization
- topic.attention
- topic.kv_cache
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/111
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/490
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 把注意力/compressor 算子迁到 TND packed-sequence 的调用约定（合轴 query、actual_seq_qlen、dequant_scale 同轴、按阶段切布局）

## 适用场景

当仓/框架把注意力布局统一到 TND（token 打平的 packed-sequence）后，需要把某个仍走 BSND/BSH 的注意力或 KV 压缩算子迁上来。迁移不是改个 layout 字符串——有一组**必须同步改的调用约定**，漏一处就 shape 报错或数值错位。

## FIA decode 从 BSND_NBSD 迁到 TND_NTD

把 MLA 模型 decode 的 [FIA](../../../concepts/kernels/fused_infer_attention_score.md) 从 `input_layout="BSND_NBSD"` 迁到 `"TND_NTD"` 时，同步改：

- **query 按 T=B*S 合轴**（打平批与序列维）；
- **必须提供按请求累积的 `actual_seq_qlen`**（TND 靠它切每请求边界）；
- **C8 量化路径的 `dequant_scale_query` 要同轴合并**（与 query 同样合到 T 轴）；
- **删除 FIA 之后原有的 `view(N, -1, kv_lora_rank)` 整形**——TND_NTD 输出已是 NTD，多余 view 会错位；
- **算子版本**：只有 `npu_fused_infer_attention_score_v2` 支持 TND_NTD + `actual_seq_qlen`；仍在 v1 的路径需**先升到 v2**。

## DSA compressor 按推理阶段切布局

DSA compressor 自定义算子（`torch.ops.custom.compressor` 及其 float8 KV epilog `torch.ops.custom.kv_compress_epilog`）**按推理阶段切换张量布局**：

- **prefill 走 TND packed-sequence**：传 `cu_seqlens`、输出 `(T, head_dim)`；
- **decode 走 BSND 批量补齐**：不传 `cu_seqlens`、输出 `(B, S, head_dim)`。

接线两阶段必须让 **position_ids/slot_mapping 生成、rope cos/sin reshape、量化 epilog 前的 flatten** 全部与所选布局一致——三者任一与布局不匹配就错位。

## 通用手段

- 迁 TND 时把「布局字符串 + 合轴 + 边界长度入参（actual_seq_qlen/cu_seqlens）+ 量化 scale 同轴 + 后处理 view 增删 + 算子版本」当成**一整组**一起改，逐项核对。
- prefill/decode 可各用不同布局（compressor 即 prefill-TND / decode-BSND），只要每阶段内部自洽。

## 风险 / 边界

- TND 算子契约（v2、actual_seq_qlen）系于当前算子版本；迁移前确认目标 commit 的算子支持 TND。
- compressor 的 prefill-TND/decode-BSND 是该 DSA 参考实现的选择，不是所有算子都要两阶段异构。

## 相关经验
- [把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse](attention_to_fia_sparse_mode_sink_window.md)
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpa](../../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md)

- TND packed-sequence 为何是仓级标准、BSND/1D shim 的约束见 [tnd-packed-sequence-standard-and-bsnd-shim](tnd_packed_sequence_standard_and_bsnd_shim.md)。
- packed/microbatch 等长假设导致的 reshape 崩见 [tnd-packed-sequence-standard-and-bsnd-shim](tnd_packed_sequence_standard_and_bsnd_shim.md)。

## Evidence

- `diff 事实`（@f573e96）：FIA decode BSND_NBSD→TND_NTD 的合轴/actual_seq_qlen/dequant_scale 同轴/删 post-view/须 v2。
- `diff 事实`（@8eae6f7）：compressor prefill-TND(cu_seqlens, (T,head_dim)) / decode-BSND((B,S,head_dim))，position_ids/rope/flatten 随布局。
- 溯源下探：[cann-recipes-infer-pr-111-feat-modify-tnd](https://gitcode.com/cann/cann-recipes-infer/merge_requests/111)、[cann-recipes-infer-pr-490-dsv4-enable-bsh-format-for-compressor-in-decode-stage](https://gitcode.com/cann/cann-recipes-infer/merge_requests/490)

<!-- cannbot:related:start -->
## 相关

- [npu_fused_infer_attention_score (v1 / v2)](../../../concepts/kernels/fused_infer_attention_score.md)（`related`）：“只有 `npu_fused_infer_attention_score_v2` 支持 TND_NTD”规定迁移所需版本，“v2 相对 v1 增加了 TND_NTD 布局支持”从算子契约侧验证该版本门槛。
- [把注意力映射到昇腾 FIA：attention sink / 滑窗 / 全窗的 sparse_mode 选择 + 推理 FIA vs 训练 FA + GQA 头数](attention_to_fia_sparse_mode_sink_window.md)（`related`）：“只有 `npu_fused_infer_attention_score_v2` 支持 TND_NTD”给出 TND 迁移的版本门槛；“`input_layout` 与 `sparse_mode` 要随注意力状态取三态”说明 MLA decode 统一 FIA 后仍要按普通、NZ 与投机解码选择布局和稀疏模式。
- [昇腾推理统一 TND packed-sequence 布局：为何是标准、BSND/packed-1D shim 的等长约束与变长崩溃](tnd_packed_sequence_standard_and_bsnd_shim.md)（`related`）：“prefill 走 TND packed-sequence”给出 compressor 的分阶段布局，“默认优先 TND（packed-sequence）布局”提供框架级标准与变长约束，可用于审查迁移是否保留错误的 BSND 分支。
- [昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpad 吃原始长度、fusion_attention TND 吃 cumsum）](../../../runbooks/runtime/mm_encoder_packed_attention_seqlen_semantics.md)（`related`）：“必须提供按请求累积的 `actual_seq_qlen`”规定 FIA 的 TND 调用要传请求边界；“走 `npu_fusion_attention(TND)` 的分支：先 `seq_lens_cpu = list(seq_lens_cpu.cumsum(0))` 转前缀和”给出从原始序列长度生成该边界的具体转换。
<!-- cannbot:related:end -->
