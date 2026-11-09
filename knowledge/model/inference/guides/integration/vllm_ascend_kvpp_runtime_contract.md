---
type: Guide
title: vLLM Ascend KVPP 预取调度：KVPPRuntime、广播完成与异常边界
description: 接入 KVPP 时核对连续缓存 bundle、attention hook、历史缓存预取和 layerwise 加载依赖，区分 Future 入队与设备完成，并检查层顺序、异常传播和清理责任。 沿 KVPPRuntime 的 create_from_kv_cache 核对整bundle广播的ready/done依赖、Future覆盖设备完成与异常清理。
aliases:
- KVPPRuntime
- KVPPScheduler
- BroadcastKVPPTransport
- _uses_layerwise_store
- KVPPScheduler.wait_for_layer
- KVPPScheduler.complete_forward
- KVPPRuntime.create_from_kv_cache：bundle与设备完成依赖
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.parallelism
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/kvpp.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kvpp.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_kvpp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/test_kvpp.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/kvpp_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/kv_cache_placement.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/kvpp_cache.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-11-02T02:11:25Z'
updated_at: '2026-11-03T07:29:07Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend KVPP 预取调度：KVPPRuntime、广播完成与异常边界

## 消费任务与版本边界

给新模型接入 KVPP，或排查预取等待、历史 KV 被覆盖和失败后状态不明时，先确认物理 bundle、attention hook、传输依赖与 forward 生命周期。固定 Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整阅读 runtime139行、广播36行、两份UT247/60行、测试辅助220行、规划器207行与分配器57行；ascend_config.py仅阅读1–111，pin为同SHA复用。源码和测试均作为数据，没有执行上游导入、线程池、UT、collective、图或NPU。

[KVPP容量指南](../optimization/vllm_ascend_kvpp_capacity_tradeoff.md)负责配置和950DT来源测量，本卡负责MRv2局部调度与完成信号，不扩大其硬件声明。[Mooncake Layerwise协议](vllm_ascend_mooncake_layerwise_protocol.md)负责外部range/session，不能用本卡的广播Future代替外部存储提交或释放证据。Main的配对Native pin为544f182d9f0c9bfe8bd7645525951d5e3692a542，与本知识任务独立Native快照不同；这里没有闭合实际Native/CANN ABI，整项硬件范围保持未知。

## Runtime先绑定连续字节，再安装hook

KVPPRuntime.create_from_kv_cache先读取KVPPConfig。禁用时size=1，启用时size=TP×PCP；size<=1直接返回scheduler=None，此分支不会继续取KVPP通信组或缓存。启用开关并不单独证明模型、connector和图组合合法，from_vllm_config也不在本方法内自动执行validate。

kv_caches未传入时，按KVCacheConfig各组layer_names读取static_forward_context[name].kv_cache，再根据组内rank创建物理计划。没有任何target owner映射时返回空runtime，不启动无目标广播。缓存名、组内rank、已初始化draft归属和底层spec接口必须先一致；完整Runner初始化顺序不由这个工厂证明。

每个target bundle以首个cache组件kv_caches[name][0]的untyped_storage为基础，把storage_offset×element_size转成字节起点，构造int8、长度为整个bundle大小、stride=1的raw view。它覆盖main与配对indexer等连续组件，长度随num_blocks增长，不是只传本轮活跃请求的KV。调用方和分配器必须提供正确连续span；这里没有逐项校验所有组件实际地址和长度。

调度层序来自tuple(layer_buffers)，沿规划器的确定顺序保存。只向这些bundle主名称的impl安装layerwise_kv_cache_hook，不分别向indexer或独立draft层安装同一调度hook。新增模型必须核对真正执行attention的位置会消费该hook，不能仅看到字段赋值就认定完整forward已经接线。分配关系在本批来源中已核对，具体地址写入及上层调用仍需目标版本验证。

## 历史缓存与layerwise分两种时机

_uses_layerwise_store只识别AscendStoreConnector及其extra_config.use_layerwise；MultiConnector只遍历直接children，使用字段的truthiness。它不是递归connector校验器，也不证明后端、角色、SDK或配置归一化已通过。

| 入口 | 非layerwise | AscendStore layerwise |
| --- | --- | --- |
| schedule_forward(has_history) | 重置层序；有历史时立即预取首个attention层。 | 重置层序；不在这里发起首层预取。 |
| wait_for_layer(layer_name) | 等待已排队Future，正常完成后推进一层并预取下一层。 | 有历史且尚无Future时按当前层名发起，再等待与推进。 |
| run_layer_prefetch | 设置线程所用NPU device后调用transport。 | 先wait_for_layer_load_ready(layer_name)，再调用transport。 |

无历史缓存时wait_for_layer直接返回，不做这段广播。layerwise路径的connector加载依赖先于广播；判断layerwise为真不等于外部数据已完成加载。普通路径按预先保存的序号推进，没有验证传入layer_name等于当前预取层名。hook调用顺序与bundle顺序不一致时，不能依靠这个方法自动纠正。

KVPPScheduler保存创建时的current NPU device、独立transfer stream和max_workers=1的执行器。start_layer_prefetch在当前计算流record一个ready event，再提交单个后台任务。单worker保证本执行器任务串行，不保证其他connector线程、通信组、进程或其他NPU stream均被串行化。

## Future覆盖设备完成

BroadcastKVPPTransport先将owner组内索引映射到kvpp_group.ranks中的global rank，广播使用kvpp_group.device_group。src不能直接填本地owner编号。每层预取依次执行：

1. transfer stream等待计算流record的cache_ready event。
2. 对整层raw byte view发起dist.broadcast(async_op=True)。
3. 调用work.wait，在transfer stream记录done event。
4. 在stream上下文外执行done.synchronize，之后transport函数才返回。

因此该任务的Future覆盖本段设备传输完成，包括owner对源缓存的读取结束，attention随后才可覆盖持久缓存。async_op=True不表示Future仅代表入队；work.wait与done.synchronize也不能互相省略后仍声称保留这里的完成合同。真正HCCL、torch_npu事件语义和跨rank失败处理需要实际配对版本验证，以上是所读实现的同步序列。

不能把该done当外部pool session commit、整步所有存储任务完成或服务请求结束。广播与模型计算能否重叠、等待位于哪个关键路径、传输全分配层带来多少流量，都需要实际时间线；没有源码证据支持固定加速比。

## 正常推进和异常清理分别核对

KVPPScheduler.wait_for_layer先Future.result，成功后才置_prefetch_future=None、递增层序并排下一层。Future异常向调用方传播，这些正常清理和推进不会执行。无历史分支返回也不负责回收先前异常留下的任务。

KVPPScheduler.complete_forward仅把_has_history设False、序号设0；没有显式取消、等待、清空Future或shutdown线程池。正常逐层等待结束时Future已由wait路径清空，但complete_forward本身不能当异常退出、提前结束或重启forward的drain保证。本卡不宣称已复现泄漏、死锁或输出错误；Agent要继续查实际Runner的try/finally、调用顺序与资源所有者。

异常探针应保留layer_name、当前ordinal、Future状态和异常、connector加载状态、ready/done事件、owner global rank及raw span。先确认所有在途传输不再访问缓存，再考虑释放或复用；不得吞掉Future异常后直接把原scratch当成下一层有效数据。

## 已读测试设计与适配验收

runtime UT使用CPU缓存、mock NPU流/事件和ManualExecutor，检查whole-bundle view、主层hook、历史开关、首层预取、layerwise等待、正常逐层推进与Future失败。测试辅助中的use_eagle判定和缓存descriptor兼容分支是测试桩，不是所有Native版本或投机方法的实际支持表。

transport UT的组rank为[4,9]、owner索引1，src应为9；receiver与owner分别检查ready等待、broadcast、work.wait、done.record及synchronize顺序，也检查36字节payload未改写40字节backing的保护区，并让synchronize时Future仍未完成。这些是源码中的验证设计，本次没有运行。

Agent接入时保存PP本地层名、bundle成员顺序、raw offset/总长度、hook覆盖、组内及global owner、has_history和layerwise开关。先核对调用顺序、非零offset、空target、首步/后续步、异常传播与资源清理，再在匹配设备上验证跨rank数值、抢占/失败恢复、图组合和时延。容量收益仍查容量卡；本卡没有NPU、真实通信、精度、性能或Agent A/B结果。
