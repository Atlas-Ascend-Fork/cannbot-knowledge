---
type: Concept
title: 在线 PD 分离：控制面、缓存传输与阶段协商
description: 在线 PD 分离推理机制：A3 等平台的多机实例、DP 请求分发与 EP 模型前向，Prefill/Decode 控制面协商、逐 CacheEntry 的 KV 传输、投机元数据及资源释放。
aliases:
- Online PD Inference
- Online PD-Disaggregated Inference
- 在线 PD 分离推理执行机制：多机实例、DP 分发与 KV 传输（Online PD Inference）
tags:
- task.implementation
- topic.architecture
- topic.kv_cache
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/kv_transfer/transfer_manager.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/kv_transfer/buffer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode_queues.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/router.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/server.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/online_inference_design.md
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:57:02Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      serving_mode:
      - online
      deployment_topology:
        all_of:
        - pd_disaggregated
      framework:
      - cann_executor
---

# 在线 PD 分离：控制面、缓存传输与阶段协商

## 入口和拓扑

当前 Executor 的在线角色为 PREFILL/DECODE，NONE 为离线；没有合并在线角色。各服务实例独立持有模型和 torch.distributed 组。父进程 spawn worker，实例 leader 提供 HTTP 与 DPDispatcher；Prefill leader 先启动 Bootstrap，Router 并发把同一请求发给选定 P/D 实例。

Router 以 bootstrap_room 对实例数取模，无 room 时生成 uuid4 低63位。它返回解析后的 Decode 结果，非200包装为 HTTPException，非JSON转502，连接错误转503；Prefill HTTP 错误本身不覆盖 Decode 主响应。直接字典可传 disagg_prefill_dp_rank，但 HTTP 请求模型不声明该字段，默认补0；多DP真实落点未必为0，不能把源码注释“留空查询”视为当前HTTP已实现。

## 控制与数据

Bootstrap 维护 `(dp,cp,tp)→rank_ip/port` 和 room→dp_rank，只负责发现与路由。Prefill 所有 rank 向 leader 注册，Decode 不注册；Decode 按请求拉拓扑并建立目标映射。注册发生在 KV 内存注册之后。local_ip 由启动参数指定，监听0.0.0.0与通告可达地址是两回事。

`KVTransferManager.register_memory` 使用缓存管理器五元组：`ptrs, data_lens, item_lens, attn_types, block_sizes`。每个 CacheEntry 的物理块大小参与传输布局；不再有全模型单一 block_size。跨TP切片逐entry校验块大小，bootstrap还校验完整 block_sizes、dtype、投机 metadata layout 和 P/D max_prefill_tokens（D上限不得小于P）。某些 draft 后端要求两端 TP/CP 一致，不能假设所有投机都支持异构并行。

MetadataBufferPool 的64字节是基础头；可附加投机 codec payload 并按对齐扩展 slot_size，发送端检查两端槽大小。不能把所有元数据槽都写成固定64字节。KV与metadata基址按HIXL要求2MiB对齐。

默认 memfabric 后端，可选 mooncake（延迟导入）采用 ascend/P2PHANDSHAKE。数据经传输引擎直写目标KV与metadata，ZMQ传握手/状态，HTTP Bootstrap不承载KV。

## 调度和生命周期

1. 每轮所有相关 rank 推进传输队列共识，再在实例内协商阶段，优先 `prefill > mm_encode > decode`。P侧可编码和Prefill，D侧只Decode；选中MM但本rank无任务时进入dummy同步流程，不调用Encoder、不写Store。
2. Prefill 请求等待bootstrap握手共识，随后进入mm_waiting_queue或waiting_queue。编码结果按请求保存，语言Prefill取得对应visual_embeddings。发送KV后进入inflight_queue；仅传输成功/失败确认并清理后释放P侧块，不能在发起传输时立即回收。
3. D侧准入统一进行最终prompt长度校验，清空mm_inputs，不做Encode。DecodePreallocQueue 分配KV和metadata槽，失败跳过等待；DecodeTransferQueue提交metadata后请求才进入running。可恢复通用draft_info并调用on_pd_restore，旧mtp_spec_tokens保留兼容。
4. Decode CP必须为1。Prefill CP映射默认仅取CP rank0；`ENABLE_ALL_CP_RANKS_FOR_TRANSFER=1` 才改走全部目标CP rank及相应应答数，不能继续将旧全CP传输描述为无条件行为。
5. 缓存压力导致空Decode批且仍有running时，驱逐最少输出、同进度最大prompt的请求并重试；finish_reason为preempted_oom，最后一个装不下为abort_oom，写finished_requests由服务分派。详见[准入/回收](../../optimizations/rules/online_decode_kv_admission_retraction.md)。

## 启动和验收

P/D各用prefill.yaml/decode.yaml，world_size为每实例；DisaggConfig由启动入口注入。默认HTTP端口P8001、D8100、Router8000、Bootstrap18800；D侧ZMQ端口统一+2避免同机冲突。多实例组长定位见[MASTER_ADDR规则](../../optimizations/rules/multi_instance_online_master_addr.md)。

先检查模型支持、每entry块布局、投机槽与并行，再验证长请求拒绝、传输失败、EOS、压力驱逐和多DP实际路由。本次未运行服务或硬件复测；设计文档仍有旧预算与元数据片段，以当前实现为准。


## Evidence

- [transfer_manager.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/kv_transfer/transfer_manager.py)（primary）
- [buffer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/kv_transfer/buffer.py)（implementation）
- [decode.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py)（implementation）
- [decode_queues.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode_queues.py)（implementation）
- [router.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/router.py)（implementation）
- [server.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/server.py)（implementation）
- [online_inference_design.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/design/online_inference_design.md)（implementation）
