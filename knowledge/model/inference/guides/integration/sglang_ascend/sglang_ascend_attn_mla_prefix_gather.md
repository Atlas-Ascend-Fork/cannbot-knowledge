---
type: Guide
title: SGLang Ascend MLA前缀读取：逐请求去页尾与NZ/FP8视图
description: 说明prefix页表展平后为何必须按请求剔除padding，及NZ物理布局、FP8字节索引和DCP重组的顺序。
tags:
- task.implementation
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/mla_cache.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/dcp/comm.py
  role: implementation
created_at: '2026-11-08T12:07:55Z'
updated_at: '2026-11-09T04:31:18Z'
platforms: []
aliases:
- build_mla_prefix_token_indices
- gather_mla_cache_tokens
---

# SGLang Ascend MLA前缀读取：逐请求去页尾与NZ/FP8视图

## 故障触发

多请求prefix长度不是页大小整数倍时，页表gather包含每个请求最后一页的无效尾部。把所有页串联后只截取sum(prefix_lens)会保留前一个请求的padding并丢掉后一个请求的真token；必须逐请求按原物理page_offset剔除尾部。

`build_mla_prefix_token_indices`逐请求累积ceil(prefix/P)*P的物理偏移，仅为每请求0..prefix-1生成索引；函数始终返回一维 int64 Tensor，页对齐时直接调用仍生成完整有效索引，全空 prefix 返回 `[0]`。Ascend 调用方仅在任一长度不对齐时构造该索引，全对齐时保留 None 以省去额外 index_select。`gather_mla_cache_tokens` 才在无物理页或索引为空时返回 `[0,1,D]`，不应伪造有效 token。

## NZ与FP8

`gather_mla_cache_tokens`先按页表读取物理页。NZ布局按[blocks,head_dim/D0,page,D0]解读，再恢复token顺序；D0普通为16、FP8为32，不能仅依据公开tensor shape直接view为NHD。FP8通过uint8 backing执行索引，完成后恢复原dtype，避免假设FP8 index_select可用。

MLA调用者在本地去尾后才做DCP历史重组；若启用ModelSlim先dequantize latent。重组保持page交错顺序，之后才kv_b展开历史K/V和计算prefix attention。

## 操作与验证

检查flatten_prefix_block_tables、各请求prefix长度与物理页尾mask来源一致；使用至少两个不对齐请求（如P+1与P-1）对照逐token逻辑历史，另外覆盖全对齐、空历史、NZ与FP8。该辅助过程带来gather和可能的重排副本，不能据此承诺prefix命中一定减少TTFT。本次未实测，平台保持未知；底层索引算子的Device闭包不在本卡范围。
