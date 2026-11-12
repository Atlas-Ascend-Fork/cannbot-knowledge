---
type: Guide
title: SGLang稀疏KV管理器的请求重置、紧凑写入与四流物化
description: 解释Host全量KV与device当前TopK缓存、v1/v2输入差别、ragged prefill、sentinel映射和hit/miss/refill/slot-map事件交接。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
- topic.implementation.synchronization
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/sparsity_driven_kv_offload/manager.py
  role: primary
created_at: '2026-11-08T11:53:41Z'
updated_at: '2026-11-08T11:53:41Z'
platforms: []
aliases:
- SparseKVCacheManager
- offload_v2
- materialize_selected_kv
---

# SGLang稀疏KV管理器的请求重置、紧凑写入与四流物化

## 池和生命周期

管理器要求MLATokenToKVPool，按req_to_token实际行数size（含padding）、max_context_len、模型latent/RoPE宽度及层数分配Host注册共享KV [size,context,1,D]，device TopK [size,K,1,D] 和slot map。slot map有size+1行，列数为(context//8+1)*8，额外行/列作sentinel，不是普通KV有效索引。

Host Tensor、host_ptr、device-visible ptr分别保留，Kernel使用最后一种地址；注册区在异步拷贝完成前必须存活。memory_saver_adapter在此明确enable=False，不能由region调用推断实际可暂停该存储。全局manager注册不等于构造/资源释放已自动完成。

请求分配hook只重置新取得slot的映射，防止新请求读旧TopK；chunked请求不会每段重置已有prefix。init_req必须在req_pool_idx已分配后调用。device缓存是最近一轮TopK的覆盖式刷新，不是源码未实现的任意容量LRU。

## v1/v2与Prefill行布局

v1把out_cache_loc当源KV槽号，适用于全native KV视图；v2接收当前forward紧凑K/RoPE，以arange作为源行，只把native loc作有效性元数据。Decode要求紧凑行与request/cache_loc行数匹配，seq_len==1沿用graph padding约定不写；req、token_pos和cache_loc有各自mask。

Prefill v2若行数等于sum(extend_lens)，按req0 token、req1 token的ragged顺序构造目标；否则要求可整除batch，解释为图式[B,tokens_per_req]并屏蔽padding。prefix_lens短于batch会补0，长于batch报错。不能把ragged写入误解为固定宽度表，也不能把out_cache_loc当紧凑源偏移。

get_forward_kv为Prefill/Extend从Host物化完整请求KV，按请求顺序拼TND并返回连续latent/RoPE，消费端用cumsum(seq_lens)作KV边界。它含.item()/Host条件与分配，不能未经验证视作无同步graph路径；源码未来resident-prefill-cache设想不是已经实现的缓存复用。

## 四流事件图

TopK允许[B,K]、[B,1,K]或[B,1,1,K]，宽度不得超过sparse_context_len。无效请求转sentinel map行，device缓存地址落0但被valid mask屏蔽；token位置需在context范围。主流构造index后记录copy_ready。

hit流等copy_ready做D2D，miss流等copy_ready用Host设备可见ptr做H2D，分别记录hit_done/miss_done；refill流等两者后把selected KV写回device缓存并记录refill_done。slot-map流等copy_ready重置映射，再只为有效TopK写当前slot并记录slot_map_done。消费selected buffer需等hit/miss，下一次可复用缓存/映射前还须等refill/slot-map。不能只等待某一路就宣称全部异步状态已完成。

## 验证与失效边界

覆盖请求slot复用、空/无效请求、重复/越界TopK、全miss/全hit、K变化、ragged与graph padding、分层offset和多流压力。先用独立native结果比数值，再测拷贝与端到端；保留精度、Host容量、缓存命中率与selected buffer临时量，不以单Kernel加速代替整条优化收益。底层地址与行复制合同见[卸载原语](/model/inference/apis/sgl_kernel_npu/sgl_sparse_kv_offload_primitives.md)。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。
