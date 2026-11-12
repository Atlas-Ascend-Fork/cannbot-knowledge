---
type: Guide
title: SGLang Ascend MiniMax-M3：按query展开的稀疏预填充与验证
description: 说明NPU块索引器、forced block合并、GQA稀疏主attention、native/FIA选择及图元数据刷新，区分GPU专属MSA优化。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
- topic.speculative_decoding
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/attention/minimax_sparse_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_prefill.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/indexer/flash_block_score_decode.py
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docker/npu.Dockerfile
  role: supporting
created_at: '2026-11-08T12:08:00Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
aliases:
- MiniMaxSparseAttnBackend
- SGLANG_MINIMAX_NPU_PREFILL_FIA
- NPU M3 sparse
---

# SGLang Ascend MiniMax-M3：按query展开的稀疏预填充与验证

## 后端选择与缓存

NPU明确关闭MSA(fmha_sm100)和GPU dense-sparse decode优化，先在捕获前探测native sparse op；实际调用仍可用移植的Triton indexer与GQA sparse attention。NHD缓存转换为页式BNSD，页大小等于稀疏K block。index cache复用频率优化仅在HIP/gfx95等guard满足时开启，不能自动用于NPU。

## Decode与forced block

decode先计算index K的block score/可选index value输出，再将TopK转换为GQA kernel所需head布局，并合并强制init/local块。init=0、local=1且index/kv head相等时可跳过通用transpose/reduce/dedup，已包含local的prefill输出不再重复append。多index head需按KV head组归并，invalid为-1，valid block限于逻辑范围。

disable_index_value时直接传req_to_token与request id，减少每层物化大页表；有index value时保留legacy page table契约。native主attention可使用每前向缓存的logical→physical表，表构建失败回到原页源。native开关和探测通过都不代表所有shape支持。

## Verify与prefill

verify将每请求draft query展成独立因果行，长度=prefix+j+1；在图外准备固定host上界，图内避免.item()，padding仍需安全page范围。仅在 disable_index_value、ndt>1 且 index query/KV 头数相等时，才将多 draft query 合入 indexer 的 head 维复用 K 读取，随后恢复请求优先 TopK 顺序，再做主 attention。与本知识库固定 sgl-kernel-npu 快照（dda6d36b0cdb4081e102d14c0a2fb276fc416e69）配套时，还须限定 score-only 的单 index KV 头：多头调用生成 bs*ndt*num_idx_heads 个长度，但该 kernel 要求 bs*gqa_group_size，即此处 bs*ndt，会触发长度断言不匹配。重放必须更新request id、逐query长度与native页表，不能复用捕获时请求映射。

普通prefill同样构造逐query长度，但indexer按变长Q块批量评分。与上述固定 kernel 快照配套时，打分仍按打包后的全局 query 行号屏蔽 key，per_query_seq_lens 仅在后续选块时消费，无法修正历史 KV 前缀或多 request 的打分范围差异；这类组合须先修复并对照 dense 参考验证。层间不变元数据只在同一ForwardBatch内复用，新前向清缓存；TBO子batch不共享旧owner缓存。主attention可用decode sparse kernel处理每query，或在开关开启且KV heads=1时使用FIA block-Q路径。SGLANG_MINIMAX_NPU_PREFILL_MAIN_BPS增大每次处理的selected blocks，>1时num_stages降至最多1以控制UB压力，仅改变softmax分组，不改变选择集合。

## 验证与边界

以上两项为 sglang dadff253c0aa8c7456b351cb9d2c282a8e513958 与固定 kernel 快照的静态接口风险。该 SGLang Dockerfile 默认下载可覆盖的 2026.11.0.post1 发布包，现有证据没有将该 wheel 绑定到上述 kernel commit，不能断言所有实际安装版本均复现相同行为。

检查dense/sparse层列表、disable-value层、score_type、forced块、TopK head映射和每query因果长度；覆盖prefix prefill、图宽→窄请求、空DP rank、多head和native开关。与dense参考比较被选集合及最终输出，并单独测indexer/主attention时间。此处复用独立kernel知识，未编译和实测，不将CUDA MSA或ROCm gfx950特性标为Ascend950支持。

## 配套知识

[GQA共享稀疏decode接口](../../../apis/sgl_kernel_npu/sgl_gqa_shared_sparse_decode.md)；[分块decode索引器接口](../../../apis/sgl_kernel_npu/sgl_flash_decode_block_indexer.md)；[分块prefill索引器接口](../../../apis/sgl_kernel_npu/sgl_flash_prefill_block_indexers.md)。
