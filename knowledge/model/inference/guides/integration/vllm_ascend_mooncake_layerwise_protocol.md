---
type: Guide
title: vLLM Ascend Mooncake Layerwise：range session、混合组与提交边界
description: "结合当前Mooncake单组/Hybrid与历史Layerwise译文核对range/session、group commit和save时机；以mamba_cache_mode='align'核对Mamba混合组。区分Prefill部署、共享buffer与真实SDK/NPU证据。5f5e25新增匹配拓扑PCP支持，旧ceac/3164及DCP/KVPP边界仍按版本保留。"
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/mooncake_hybrid_attention.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/mooncake_layerwise_adaptation_and_optimization.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/mooncake_hybrid_attention.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/mooncake_layerwise_adaptation_and_optimization.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/layerwise_kv_pool.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/kv_cache_pool_ascend_store.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/ascend_store_connector.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/memcache_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_layerwise.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/layerwise_cache_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/pool_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/preempt_offload/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/sparse_kv_offload/sparse_kv_offload_manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/distributed/kv_transfer/utils/mooncake_transfer_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/mooncake_hybrid_attention.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/docs/source/user_guide/feature_guide/mooncake_layerwise_adaptation_and_optimization.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/layerwise_keys.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/5f5e25dd94db85b59251be7d3baf7c808475b6d7/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_backend.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/coordinator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_kv_cache_coordinator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/kv_transfer.py
  role: implementation
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-11-04T03:35:06Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Mooncake Layerwise：range session、混合组与提交边界

## 状态与前提

draft：固定两份设计明确真 NPU、Mooncake 服务、多进程/分布式和性能验证尚未完成。使用 AscendStoreConnector backend=mooncake、use_layerwise=true，客户端需 put/get session start/ranges/end/revoke APIs。方法存在检查可尽早失败，但不能代替固定 SDK/ABI/返回码版本。

## 对象和 range 语义

单组每 block/storing-rank 一个包含多层的对象，约从 B×L×R 个对象变为 B×R，payload 总量不变。offset 来自真实每层多 cache entry 字节前缀和，不是 layer_id×统一page_size，也不能再乘层数。缺失 range、返回条目数或类型不符必须失败，不静默当成功。

完整 put 后 commit 才可读，失败 key revoke；request/key 的多个 owner 释放到最后一个才 get-end。chunked 后续步可用新的本地 block ID 恢复已提交前缀，retry 保留必要关系，terminal/preempt 清理。get 失败必须按相应单/多组策略停止消费或通知重算，不能使用半份KV。

## Hybrid 可达性与物理层

hybrid namespace 包含布局digest、group、block coverage、hash/head；digest 不是权重校验或租户认证。每对象只存所属组，group-local layer 控制远端offset，physical layer 控制 compute event。raw-token block coverage 已在 runtime spec 中，不能再乘压缩率。

只有所有必要 stage/head/group 快照都 committed/readable 才形成共同可达 token 边界，full-attention hit 不能替代 window/compressor state。每组在自身最后层提交，session owner 含 request/group/logical block；稀疏 state 不能被当连续前缀。Mamba/GDN/KDA align state 需 compute 后 save，不能在 entry 前发布旧状态。单组旧文的 recurrent 禁止与后续 hybrid align 规则需按实际实现分支区分。

## 混合状态恢复入口

恢复前先确认实际vLLM/Ascend版本及注册的manager，按[混合缓存补丁](vllm_ascend_hybrid_cache_patch_contract.md)和[KV Pool共同可达性](vllm_ascend_kv_pool_metadata_reachability.md)执行共同命中裁决。ceac的layerwise scheduler把各必要stage/head/group的readable候选交给`AscendStoreCoordinator.find_reachable_hit_tokens`，再由`find_longest_cache_hit`调用实际单类型manager，按各组spec、对齐和状态约束收缩共同长度。只有该返回长度及对应group mask才可作为恢复入口；不能根据各组coverage、独立最大hit或readable=true自行选前缀，也不能先拼接各组最大值再补检查。未确认实际manager返回或等价共同可达门控时，不认定正长度前缀可恢复，按该版本的重算/失败路径处理。[ceac共同查找实现](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/coordinator.py#L282-L426)

独立Native `5df63a7203cdb9328d824a27b682e77c7b9928be`与ceac配套Native `544f182d9f0c9bfe8bd7645525951d5e3692a542`的证据必须分开；本次未验证后者实际Native ABI，不能用独立版本的manager结论补成配套部署保证。ceac的AscendHybrid补丁另协调私有tail对齐、Eagle及跨组hit，不能绕过实际安装和绑定。本次只读对照确认上述共享coordinator与下述返回码消费者在3164、5f5e25仍为相同函数结构；后续PCP支持仍按文末独立条件，不把ceac补丁的PCP=1限制或任一Native接口泛化到后续版本。

返回码按操作分别解释：Backend对每key结果要求等长整数序列，拒绝bool、非整数或条目数不符；`batch_is_readable`只接受0/1并把1映射为可读。range `batch_copy_put/get`由传输线程以`result<0`判失败，正值不能因此算失败，也不代表对象已经提交；`batch_commit`只在`result==0`时记录提交，任何非0结果都进入失败/revoke处理。不能统一套用“nonzero失败”或“ret>=0即全部成功”到这些不同阶段。copy-put失败key撤销并退出后续提交，copy-get失败块标invalid并从后续层range加载集合移除；仍需沿原有错误/重算与drain路径收尾，不能消费半份状态。[ceac范围传输与提交](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/kv_transfer.py#L898-L951)；[GET失败标记](https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/layerwise/kv_transfer.py#L1190-L1233)。这些是固定源码合同，本次未运行外部SDK、服务或NPU验收。

## 流水与验证

cache-ready event 保护旧计算/写入，future get、current put 在 Attention compute window 调度；bounded队列可能与后续 O-proj/HCCL/EP 竞争，不是全局带宽调度。首个 demand load 仍阻塞。整步结束等待包括最后无 range 层的 pending PUT，异常退出 drain 后再释放 session。

先 TP1 eager、隔离 pool，再增加TP/chunk/prefetch，逐组对齐冷/热 token、KV range与commit。ceac/3164的Hybrid topology-matched PP 可有不均分区，PCP/DCP/TP mismatch 不支持；后续5f5e25的PCP条件见文末，图仍另验。关闭 range debug 后测TTFT、传输尾部与HCCL。来源CPU/mock结果不作为本仓结果，也不填 verified；真机验收前不升稳定硬件结论。


## 中文单组与Hybrid说明的版本冲突

mooncake_hybrid_attention.po的33条及mooncake_layerwise_adaptation_and_optimization.po的62条译文均对应当前英文，但英文之间仍有时间层次。单组适配分析引用个人branch/0a023b...和旧PR，后续Hybrid说明引用be4270...；这些是文档描述的历史基线，本卡证据仍冻结在ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，不自动切换本次源码。

旧文仍列recurrent Mamba拒绝、把hybrid/PP作为P2计划；后续Hybrid说明和所读pool_scheduler._infer_mamba_groups要求MambaSpec的mamba_cache_mode='align'，worker识别align-state组并以post-compute save。应按后续Hybrid分支判断，不能继续把全部Mamba或PP一律当未来功能，也不能因此开放PCP/DCP、TP mismatch或空projected cache组。topology-matched PP、stage-local group和独立draft层均需实际模型/配置验收。

这一路是AscendStoreConnector的backend=mooncake、use_layerwise=true，不是P/D MooncakeLayerwiseConnector。与Memcache共享coordinator不意味着Mooncake range调用变成MemFabric GVA操作，两个SDK/内存注册合同分开。

## key、group、字节与提交的独立边界

单组B×L×R变B×R只减少对象/key/session和存在查询项，不减少KV payload总字节。block_len前缀和与group_layer_cache_entry_offsets决定实际range，layerwise_max_transfer_blocks限制key/block行，layerwise_max_transfer_bytes拆大连续segment，不能假定它就是整call总字节上限；自适应总bytes/ranges、滑动session窗口与本地fan-out仍是来源优化方向，不当已实现收益。

Hybrid使用mooncake_hybrid_v1布局namespace，TP、有序group membership/page签名参与digest；group-local层算offset、physical层选event/完成，group在自身末层commit，不必等模型末层。raw tokens/block已经含覆盖，不能再乘压缩率。不同权重但同名同规格仍需隔离池，layout digest不是checkpoint checksum或租户身份。

batch_is_readable与共同可达边界要求所有必要stage/head/group可读；full-attention hit不能代替窗口/压缩状态。owner含(request_id,group_id,logical_block_index)，不同组的block0不能覆盖会话身份；后续chunk以当前本地块ID恢复已commit数据，不能复用过时地址。

## get失败、推进游标与算子窗口

所读worker先发布abort/invalid状态；Hybrid异常分支取消gate，先尝试full drain，再调用_finish_current_layerwise_load_sessions。该分支对drain异常使用suppress，调用顺序本身不能替代外部range已退出的证据。单组分析的invalid-block重算说明不等于所有Hybrid错误都可无条件继续forward。get_block_ids_with_load_errors会复制并清空当前错误集合，消费方要保留实际错误证据。consumer-only角色在load hook推进current_layer，不能依赖不会触发的save hook。

普通full/SWA在entry处的ready event后提交PUT；Mamba/GDN/KDA等attention内部更新状态的组必须post-compute保存，避免发布旧状态。最后物理层无range也要drain早先PUT，调度器释放preempt/finished请求块后、下次forward复用前的保存fence与层内event职责不同。

默认future GET继续排队、最多八个SEND未完成是内部queue policy，不是可随意填写的公开参数，也不是集群带宽调度。正文允许传输尾部与后续O-proj/HCCL/EP重叠，而其validation清单又要求观察后续HCCL前完成；后者不能被当成当前代码已全局串行化的保证，应在所有相关stream/rank的实际trace检查竞争。首个未预取demand load仍需attention前完成，metadata RPC不是payload DMA。

## 客户端与测试声明

七个session/range方法存在检查不能证明外部Mooncake ABI、结果长度/返回码、可读查询适配或真实服务兼容。ReplicateConfig中的preferred_segment/prefer_alloc_in_same_node、placement和提交状态单独核对。来源285 passed/106 subtests及旧环境变量0/1测试仅是历史CPU/mock报告；迁移additional_config.kv_pool_range_debug尚未runtime验证，不能用旧结果给新配置填verified。

诊断用bool kv_pool_range_debug，性能对照关闭该项与profiling；固定prefetch=2、64块/16MiB拆分是示例，不是DeepSeek-V4内存容量或性能承诺。真实NPU、Mooncake Master/Metadata、并发/抢占/服务失败与分布式验收仍独立，本批未运行这些服务或上游测试。


## 历史Layerwise KV Pool单页不作为当前全局限制

layerwise_kv_pool.po的48条译文没有同名当前英文。其“仅memcache、Mooncake不支持use_layerwise”“多组Hybrid未支持”“所有基本full attention未集成”等叙述不能覆盖本卡当前两份Mooncake单组/Hybrid设计与已读实现。反过来，Mooncake range/session存在也不为Memcache共享物理buffer提供completion provider，不能扩展共享Prefill复用范围。

旧文把save统一写在attention后；当前普通full/SWA可在entry-ready后提交PUT，而内部改变state的Mamba/GDN/KDA仍需post-compute。这两个时机由缓存写入边界决定，不是一个通用after-attention规则。layerwise_max_transfer_bytes按实际连续segment拆分，不据旧表宣传整call的总bytes严格上限。

旧mooncake_rpc_port端口与0自动分配说明按[当前KV Pool本地IPC](../deployment/vllm_ascend_kv_pool_backends.md)处理。旧kv_both/producer/consumer和代理说明只保留历史路由语境；当前通用部署表将Mooncake/Memcache use_layerwise限定Prefill，具体consumer-only协议路径仍需对应设计/构建验收，不能仅凭hook或角色名启用任意D端layerwise部署。无proxy的mixed例与需要metaserver的PD逐层路由分别检查可达地址。

layerwise_prefetch_layers、h2d_stagger_us和批量参数是调参候选：更多prefetch可增加在途内存，延迟stagger可能减少竞争也可能增加等待；1–4或100微秒示例均不保证收益。先固定模型布局/SDK/角色，取真实event、传输尾部和TTFT/TPOT；本次没有外部Mooncake或NPU实验，draft与空平台保持。


## 3164固定增量：Layerwise子类、Backend与PD元数据

本节固定Main `3164adc8fe75892fbf7f99f524bb72fddf1e6efd`。与ceac相比，pool大文件主要拆出layerwise子类；同AST函数跨文件精确复用，只提取实际变化，不把新路径误报成整套新协议，也不声称外部Mooncake/Memcache、NPU或并发测试已运行。

AscendStoreConnector通过factory选择KVPoolScheduler/Worker或LayerwiseKVPoolScheduler/Worker。Backend registry现在解析具体class，class持有layerwise_data_plane、bind_layerwise_keys、partial-key与fence/backlog接口；不再通过独立protocol模块统一转发。默认Backend的lazy初始化是no-op、layerwise key接口明确NotImplemented。未知backend class为None或不具备block_key/gva能力时，Layerwise scheduler构造显式失败，不能靠use_layerwise字符串认定协议可用。

Mooncake class提供block_key与send backlog=8，继续拒绝PCP/DCP>1和layerwise TP mismatch；Memcache class提供gva。重用layout只对已开启use_layerwise的gva后端选取，不再把所有layerwise protocol都当共享物理buffer复用。memcache_dp_init_barrier参数和相应DP初始化barrier在该版本移除；不能保留旧配置声称仍执行该同步。

Layerwise worker保留session、GVA、attention窗口和DSpark prefix职责；普通worker不再承载这些层级状态。普通set_external_slot_release_waiter直接False，layerwise类另保留实际接收线程的waiter。connector对同一physical layer只等待一次load，step绑定metadata时重置_loaded_layer；Mamba后续copy仍独立执行，不能由“本层已wait”推整个状态生命周期都完成。

Layerwise get_finished先full drain后释放本步lease，block-key还清理finished/preempt请求owner，再调用普通完成收尾。GVA重复key查找改为setdefault保留第一个位置，不能据此承诺所有重复key自动fan-out。普通scheduler在含不可缓存私有组时，以prompt_len−1向下对齐传输粒度；block-key非Eagle有同样保守前缀边界。未调度async请求从新请求和cached请求中排除后才继续load，避免只看已完成请求列表。

P/D Mooncake仍是另一条接口：prefill截断后会清空并重算block hashes；完成do_remote_prefill请求时按remote_host/port/request_id通知接收线程并清该flag。缺线程是显式错误，缺远端字段只告警，不等于payload已成功传完。

P/D cache注册为普通full/SWA辨别HND与NHD；仅单KV head且每block字节连续的NHD可作为等字节HND描述，多head歧义或不匹配拒绝。MLA、circular和SFA indexer有独立布局分支，不能统一transpose所有cache。tp_replicated Mamba不做TP分片，要求local/remote shape与block长度完全相同；非replicated仍要求整数TP比例。这里只闭合所读增量和调用约束，跨rank组合仍待验。

preempt offload按resolve_dcp_kv_block_size换算组块大小，CPU coordinator固定pcp_world_size=1；移除旧PCP/DCP都为1的断言不代表任意CP组合已实现。Sparse offload新增top-k scratch组件清单供zeroer排除，GlobalTE unregister不再预先断开所有peer；资源注册/完成/对端不再访问仍不能靠函数返回名推断。

## 2026-11-03 发布快照：PCP 已有独立条件

本节固定发布候选源码 `5f5e25dd94db85b59251be7d3baf7c808475b6d7`，并核对本次抓取的中文 HTML；前文拒绝 PCP 的结论分别适用于 ceac/3164，不能用于这个后续版本。公开发布身份和逐页内容证据见[文档渲染核验](../../runbooks/validations/vllm_ascend_document_rendering_evidence.md)。文档和静态实现对应，不表示设备验收已经执行。

后续 Mooncake layerwise 文档允许 producer/consumer 的 TP、PP、PCP 相同，示例为 MRv2 DeepSeek-V4-Flash、PCP4、DCP1、block32、MTP3、`use_layerwise=true`。DCP>1、P/D TP mismatch、PCP 加 `enable_kvpp` 层分片仍不支持；不能把这个变化扩成任意上下文并行组合。MambaSpec 的 align state 与 PP 空 projected group 限制仍分别成立。

每个 PCP worker 保有独立 session，key 追加 `@pcp_size:<size>@pcp_rank:<rank>`；PCP1 的旧 key 不变，不同 PCP size 隔离。命中要求所有必要 PP stage、PCP rank 和保存 TP/head 的对象均 committed。TP-replicated MLA 在每个 PCP rank 内仍按 head 单写，recurrent state 保留每 TP key；PCP 不再乘逻辑 group/hash block 大小，但每 PCP rank 各存一份，容量与传输带宽须据此累计。

先 eager，再以 FULL_DECODE_ONLY、主/Indexer FP8、async、MTP 和超过 batch token 预算的 prompt 验收；关闭本地 APC 后重复请求，比较无远端传输基线，并注入缺失 rank 对象确认重算。中文旧测试清单中的 `TP=1/2` 在本次 HTML 被智能排版显示成 `TP=½`；它不是 TP=0.5 配置，按固定英文源码读取。
