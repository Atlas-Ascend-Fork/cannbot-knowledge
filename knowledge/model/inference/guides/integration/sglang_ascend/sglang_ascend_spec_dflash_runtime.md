---
type: Guide
title: SGLang Ascend DFlash循环：target hidden物化与图回退
description: 说明DFlash草稿借用target head、上下文KV物化、私有滑窗request表，以及NPU禁用GPU融合准备和DP草稿图的实际边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.kv_cache
- topic.graph_execution
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_worker_v2.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_info.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/speculative/dflash_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
created_at: '2026-11-08T12:08:06Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
aliases:
- DFlashWorkerV2
- DFLASH NPU greedy fallback
---

# SGLang Ascend DFlash循环：target hidden物化与图回退

## 草稿依赖target上下文

DFlash使用普通TpModelWorker驱动draft，由target hidden物化draft KV，没有Eagle的draft/draft_extend拆分。draft借用target embedding/LM head，block size由解析后的num_draft_tokens设定；mask token只作输入，其embedding行边界与可采样词表不同。草稿结果仍需target verify，不能仅按draft logits提交。

无draft window时复用target request→token映射和分配状态；开启window后维护私有compact表，但仍处于相同全局KV index空间，保持prefix命中可复用。compact表不能被误认为独立token allocator。

## NPU物化与回退

target hidden 注入仅对 isinstance(attn, DFlashMLAAttention) 调用 write_context_kv。非 MLA 的 prefill 顺序物化（无 cache_loc_2d）在 NPU 调 forward_prepare_npu，应用 V scale，再以 physical KVWriteLoc 顺序写 draft 池。decode 调用传入 cache_loc_2d 的 prefix-valid 分支：非 MLA 走 kv_proj_only→apply_k_norm→apply_k_rope，再用 store_prefix 按 commit_lens 写入有效前缀，并非 forward_prepare_npu 分支。GPU融合KV materialization、prepare block、accept bonus和compact rebuild只在CUDA/HIP/XPU启用，NPU走分步/参考路线；legacy compact重建可能有nonzero和max().item()主机同步。

draft graph在DP attention启用时关闭，处理idle/不等DP batch走eager。target verify图是另一阶段，仍由最终ForwardBatch判断；DP extend-in-batch、idle rank等有额外限制，不能因draft图关闭推断target图也全部关闭，反之亦然。NPU的verify元数据由post-pad ModelRunner初始化，避免提前skip。

## 输出语义与验收

NPU selector sampling关闭，DFlash非greedy验证不可用时worker记录warning并回退greedy argmax；请求的采样分布不会被保持。与DSpark的NPU chain sampling区分，部署配方不能把两者互换。只有无grammar/logprob/penalty等条件时才可省去完整target logits gather，默认不能把greedy shortcut用于需分布信息的请求。

检查target/draft buffer alias、context物化的位置与V缩放、window重建、DP idle、接受数量和后续KV。测量应包含物化、compact重建与验证时间，而非只测draft网络。本次未跑模型、图或分布测试，具体型号兼容未确认。
