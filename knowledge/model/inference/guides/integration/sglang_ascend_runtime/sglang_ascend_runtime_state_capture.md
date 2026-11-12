---
type: Guide
title: SGLang NPU Indexer与专家路由回读的容量和并行合同
description: 说明Indexer只支持DP attention、Host/Device int32缓存预算、专家scattered路径all-gather、draft隔离和拷贝事件后的finalize。
tags:
- task.implementation
- topic.reinforcement_learning
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/state_capturer/indexer_topk.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/state_capturer/routed_experts.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/state_capturer/base.py
  role: implementation
created_at: '2026-11-08T12:20:20Z'
updated_at: '2026-11-08T12:20:20Z'
platforms: []
aliases:
- IndexerTopkCapturer
- RoutedExpertsCapturer
---

# SGLang NPU Indexer与专家路由回读的容量和并行合同

Indexer producer只接CUDA/NPU；enable_return_indexer_topk开启且indexer层数/topk正才构建。构造要求attn_tp_size==1，源码称仅DP attention，不能据NPU可创建推广到任意TP。设备缓存按rank本地max(chunked_prefill_size,max_running_requests)×indexer_layers×topk分配int32，Host缓存num_tokens×layers×topk也需4字节/元素。

RoutedExperts的设备buffer跨DP拼接，max batch要乘num_dp_ranks，宽度还包括fused shared expert；返回Host只保留routed topk列。仅输出rank分配缓存，但scattered A2A后端deepep/deepep_v2/ascend_ops的其他rank仍必须参加attention-TP all-gather，不能因无Host cache跳过collective。非scattered DP通过Host本地slice避免设备标量同步。

专家capture还区分TBO child的parent token区间和DP偏移；draft TopK显式禁用向target全局buffer写，HashTopK不改。源码FIXME指出spec verify token数尚未计入max batch，开启投机与回读需额外检查容量，不把一般max_running_requests公式当完整上界。

TopkCaptureOutput先在结果copy流将out_cache_loc/topk复制，copy_done同步后才finalize写Host缓存。Host pinned缓存通过平台allocator分配，NPU不是CUDA host-register。API输出为base64编码int32字节，消费方按实际seq/layers/topk重排，不能用字符串长度推断token数量。

验收检查DP>1、batch/chunk上界、target/draft、TBO、shared列裁剪和输出顺序；回读会增加HBM/Host占用与通信，开启前后分别测性能，不把训练调试辅助输出当免费能力。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
