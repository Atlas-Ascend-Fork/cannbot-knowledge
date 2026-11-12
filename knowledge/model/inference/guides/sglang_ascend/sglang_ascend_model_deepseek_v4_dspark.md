---
type: Guide
title: SGLang 昇腾 DSV4 DSpark draft 的 attention 与加载限制
description: 说明非压缩 draft、Q head norm、BF16 wo_a、分 stage 词表权重与 ModelSlim shared fusion
  排除条件。
tags:
- task.implementation
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4_dspark.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/deepseek_v4.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/utils.py
  role: implementation
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-09T04:34:34Z'
platforms: []
---

# SGLang 昇腾 DSV4 DSpark draft 的 attention 与加载限制

## draft 专用机制

DSpark attention 构造强制 compress_ratio=0、关闭 fused wqa/wkv 和 FP8 wo_a，并令 wo_a 不保留 quant_config。Q head norm 关闭时仅执行对应 RoPE；开启时 NPU 用 cached ones 调用 RMSNorm，再通过 Dsv4NpuRoPE 完成旋转。输出 inverse RoPE 后，NPU 以 FP32 einsum 计算 BF16 wo_a 并转回 q dtype，不能套 target 的 MXFP8 absorb 投影。

idle rank 的 attention 返回零形状结果，后续 shared MoE 仍参与 collective。源码多流分支仅在 SGLANG_OPT_USE_MULTI_STREAM_OVERLAP 与 SGLANG_DSPARK_ENABLE_MULTI_STREAM 同时开启、torch.cuda.is_available() 为真而构造 alt_streams 后，才于 capture/小 token batch 分流 KV/Q 并等待 KV stream。常规 NPU LLM 初始化将 torch.cuda.is_available 设为 False，因此该分支不能作为当前 NPU 可达的并行机制；head padding 的计算结果在输出裁回实际 n_local_heads。

## 权重与融合限制

旧架构 NPU 与 arch35 的 DSpark checkpoint 名称映射不同。拥有独立词表模块的路径只从 stage0 加载 embedding、末 stage 加载 lm_head；其 ModelSlim loader 不支持把 shared experts 映射到 fused expert slots，模型类明确返回禁用原因。不能仅按 target 支持 shared fusion 推给 draft。

验证 stage→参数名、confidence head 是否完整加载、target/draft 的不同 wo_a dtype、idle 与多步 positions。切换 fusion 或量化应按新方案重新加载对应 stage 权重并刷新派生 norm 缓存；既有 KV 内容能否复用需核对其生成语义。来源 load_weights/post_load_weights 没有要求这些变化必然重分配 draft pool，池重分配应由布局、dtype 或容量等实际几何变化决定，不能无条件推定；当前摄入未运行 DSpark 推理或测量 speculative 加速。
