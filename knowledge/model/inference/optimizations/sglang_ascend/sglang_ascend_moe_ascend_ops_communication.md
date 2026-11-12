---
type: Optimization
title: SGLang ascend_ops 的 prefill 与 MC2 decode 通信
description: 说明 AllGather/AllToAllV prefill、MC2 可配置容量 decode、padding 缓冲复用与 combine_quant_mode
  的真实值。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/token_dispatcher/ascend_ops.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/utils.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/moe/moe_runner/ascend.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/arg_groups/moe_hook.py
  role: supporting
created_at: '2026-11-08T12:01:09Z'
updated_at: '2026-11-09T04:36:38Z'
platforms: []
---

# SGLang ascend_ops 的 prefill 与 MC2 decode 通信

## 模式与并行前提

ascend_ops 按 extend-in-batch 选择 prefill；默认 AllToAllV，可选 AllGather，decode 使用 low_latency MC2。AllGather 需要 TP=EP、连续 expert placement，并拒绝 fused shared experts。prefill AllGather/AllToAllV 调用 _quant_mode("routing") 时未传 dtype_mode，只读 generic dispatcher_output_dtype，缺省 BF16；MC2 decode 才传 low_latency，先读 low_latency_dispatcher_output_dtype 再回退 generic，缺省同为 BF16。不能仅按 checkpoint dtype 推断通信格式。

AllGather 先交换各 rank 实际行数，再 pad 到最大行数，gather payload、weights、IDs 与 scales 后剥离 padding，支持 CP/DP 导致的不等长 rank；全局零 token 会拒绝。combine 在 FP32 贡献上 ReduceScatter，再裁本地实际行数并恢复输入 dtype。AllToAllV 交换 histogram/counts、计算 send/recv splits，payload 与 raw scale bytes 一起通信；`.cpu().tolist()` 产生 host 同步成本。

## MC2 容量与量化

decode 仅在 `SGLANG_DEEPEP_NUM_MAX_DISPATCH_TOKENS_PER_RANK` 非零时使用固定 pad capacity，并在实际 token 超限时报错；设为0时按本次实际 num_tokens 派发，不采用固定padding容量。缓冲按 `(pad_bs,H,topk)` 缓存，写入实际行并清理上次有效尾部，x_active_mask 屏蔽 padding。MC2 dispatch 的 BF16/INT8/MXFP8 mode 为 `0/2/4`，MXFP8 需 H%64=0 并使用 paired scales；combine 当前明确 `comm_quant_mode=0`，不能照搬其他实现的 mode=4。

## 使用、代价与验证

先固定 backend 与合法 JSON config，再对比两种 prefill 的通信量、host 同步与不均衡 token 开销；decode 检查 capacity、mask 和同一轮 dispatch/combine state。回退需重建 dispatcher，清除陈旧 state。`fused_op` 虽出现在 choices 中但配置验证明确拒绝，尚未实现。当前来源没有本次收益测量。
