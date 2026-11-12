---
type: Guide
title: SGLang Ascend DCP页交错与稀疏索引本地化
description: 按物理页计算DCP所属rank、局部长度和verify链前沿，说明全局TopK过滤压紧及保序要求。
tags:
- task.implementation
- topic.attention
- topic.parallelism
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/layers/dcp/layout.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dcp_metadata.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/dsa_dcp.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/forward_batch_info.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv/alloc/runner_ids.py
  role: implementation
created_at: '2026-11-08T12:07:54Z'
updated_at: '2026-11-09T04:31:21Z'
platforms: []
aliases:
- remap_dcp_sparse_indices
- get_dcp_chain_spec_lens
---

# SGLang Ascend DCP页交错与稀疏索引本地化

## 适用场景

NPU MLA/DSA DCP用page_size作为interleave_size；不能直接把GPU某些DSA索引池按token取模的分片规则套进来。令页大小P、DCP规模W，周期为W*P。全局位置p的owner为floor(p/P)%W；本地位置为floor(p/(W*P))*P+p%P。本地有效长度由完整周期加本rank在尾周期获得的clamp余量组成。

## Verify链与TopK

`get_dcp_chain_spec_lens`先按请求优先展开宽度Q的因果前沿，从totalKV-Q+1到totalKV，再换算每个前沿的本地长度。totalKV不足以容纳整条链时生成零有效长度，不能把padding前缀误作真实历史。dense MLA由这些长度构造bool掩码，True表示屏蔽。

`remap_dcp_sparse_indices`对已全局选好的TopK判owner：本rank保留并转成本地索引，其他rank置-1；再稳定压紧有效项，保留原score顺序。源码为了Ascend除法/余数性能在部分计算使用FP32，因此不要无证据外推到超出浮点精确整数域的任意超长位置。

## 检查与边界

核对full allocator地址、attention局部页表和indexer全局写地址是否属于同一索引空间；先选全局TopK再localize，而且每批新TopK只做一次。已经本地化并被层间共享的结果再转换会破坏位置。

建议覆盖P-1、P、W*P-1、W*P等边界、没有本地KV的rank、TopK全非本地、负sentinel和verify多步因果；比较各rank有效数量之和是否等于全局可见数。压紧与转换增加设备操作，换来分片缓存可寻址性；它们不负责实际attention合并或所有权分配。本次仅阅读源码，硬件和超长域未实测。

## 调用依赖补充

ScheduleBatch及req_to_token保存allocator-global slot，IterationIds窗口也在该空间。NPU DCP target在ForwardBatch.init_new先将原out_cache_loc保存为origin_out_cache_loc，再由 `IterationIds.bind` 使用 RunnerIds 提供的本地化 IdSpace，将 target 写窗口绑定为 rank-local slot（其他rank为-1）；复制的draft池和DSA indexer仍消费global身份。RunnerIds保留_call_spaces供计划外消费者使用，不能在池的公共id空间上整体替换成local映射。padding及轻量inner view必须同时携带origin_out_cache_loc，避免graph replay丢失indexer全局写地址。
