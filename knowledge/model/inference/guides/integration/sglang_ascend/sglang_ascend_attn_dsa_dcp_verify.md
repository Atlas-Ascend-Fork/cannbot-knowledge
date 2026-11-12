---
type: Guide
title: SGLang Ascend DSA DCP验证：逐query因果行与局部稀疏attention
description: 将固定宽度投机验证展成请求优先的独立query行，说明PA_BSND页表、非因果本地稀疏模式和LSE恢复。
tags:
- task.implementation
- topic.attention
- topic.parallelism
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dsa_dcp.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/dcp/layout.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/dcp/comm.py
  role: implementation
created_at: '2026-11-08T12:07:55Z'
updated_at: '2026-11-08T12:07:55Z'
platforms: []
aliases:
- forward_dcp_sparse_attention
---

# SGLang Ascend DSA DCP验证：逐query因果行与局部稀疏attention

## Verify为何要逐query展开

DCP下同一请求的不同draft query具有不同局部KV前沿，不能用请求末尾长度替代所有行。verify以请求优先顺序展开成bs*draft_width行，每行一个独立query；block_table行数和本地KV长度数必须与query行一致，否则assert失败。实际query累计边界为int32的1..rows；非verify也显式转int32。

## 调用与掩码语义

`torch.ops.npu.sgl_sparse_flash_attention`接收TND query、PA_BSND缓存、sparse_block_size=1和attention_mode=2。此处sparse_mode=0是有意选择：全局TopK已经完成因果选择，localize后索引顺序不再保留全局位置语义，不能再次使用以本地索引推导因果性的模式。

返回的softmax_max和sum先转换FP32，再计算自然对数LSE=max+log(sum)，并permute到DCP合并需要的token/head布局。这里只得到rank-local部分输出，调用者仍须执行跨rankLSE合并，不能直接视为最终attention。

## 验收与回退

先检查TopK已localize且sentinel合法，之后检查逐行页表/长度/Q边界一致，最后对比DCP=1的verify各位置输出。重点用同一请求draft各步跨越物理页owner的样例，才能发现“所有行复用最终长度”的前视泄漏。本次未运行数值测试；不满足逐query元数据时应回到已支持的非DCP路线或修复调用方，不应静默广播错误长度。平台范围仍待明确证据。

## 配套知识

[稀疏attention接口](../../../apis/sgl_kernel_npu/sgl_sparse_flash_attention.md)。
