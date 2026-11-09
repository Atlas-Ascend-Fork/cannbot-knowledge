---
type: Runbook
title: vLLM Ascend 稀疏 Offload：共享层缓冲复用等待与丢失 ACK
description: 区分 Memcache save、远端读完成、请求终态和热缓冲 H2D，排查共享物理槽被过早复用或无限等待的机制。
tags:
- task.debugging
- topic.kv_cache
- topic.memory
- topic.data_movement
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/layerwise_and_sparse_kv_cache_offloading.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/layerwise_and_sparse_kv_cache_offloading.md
  role: constraint
created_at: '2026-10-29T11:00:26Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T11:00:26Z'
---

# vLLM Ascend 稀疏 Offload：共享层缓冲复用等待与丢失 ACK


## 触发与支持边界

A3 PD 的共享层 offload 中，P 端后续层长时间等待，或复用后 D 出现错误 KV。整体部署边界来自[稀疏 offload 指南](../../guides/integration/vllm_ascend_sparse_layerwise_offload.md)：PD-only，非HYBRID，D主KV BF16，MemFabric协议及正确两端配置；950 sparse offload 不支持。这里是设计级诊断，未取得现场trace或复现。

## 以物理槽追踪两个消费者

若cache-bearing层共N、独立层I、共享层R=N-I、共享槽数B，主缓存物理份数为 I+min(B,R)。仅在每层大小一致时可按这个比例估算主KV节省，不能连同indexer或全部HBM套比例。复用轮转必须保持兼容layout，MTP层也要纳入。

某物理槽写入下一逻辑层前，必须同时等 MemcacheSave 和 D 端远程读取完成。探针记录物理存储身份、逻辑层、请求/TP contributor、save完成、remote-read-ack与下一次write；只按逻辑层名建 gate 可能放过同槽仍在使用的旧数据。

## 超时和错误路径的区别

MF_META初始握手有100秒超时；每层 remote read 完成 gate 没有总体deadline。ACK丢失而sender仍存活时 P 可一直等，不能因握手timeout存在就推导所有gate都有100秒上限。READ_FAILED需使目的数据失效并把错误告知sender，该connector不自动重试read。

非对称TP要求P>=D且整除：P rank映射 D rank=prank//ratio、contributor=prank%ratio。主KV复制时仅member0发送，indexer贡献片合并；某contributor本次零块也必须完成ack。检查所有预期contributor，而非仅有数据发送者。

MultiConnector优先调用Ascend completion provider，不能按JSON子connector顺序猜回调顺序。单物理槽可复用完成，也不等于全请求各rank已终态、D可decode；两类完成必须各自聚合。

## 进一步分层定位

D端主KV在TP共享pinned host池，indexer留在NPU；topk miss走H2D并维护logical→physical热槽映射。普通CPU tensor不能替代已注册CPU视图。等待若发生在D热缓冲阶段，核对注册、LRU与所需H2D，不能仅看P save日志。

校验两端memfabric_transfer_protocol一致；device_urma可被connector识别不代表950支持sparse功能。不要通过删除reuse gate、伪造ACK或把失败块标成hit来恢复进度。可在隔离部署回退不复用/无offload路径，保持容量可容纳；验收要覆盖零块contributor、取消、失败通知、跨层复用及输出一致，随后再比较RAM/HBM与时延。本次未执行这些设备实验。
