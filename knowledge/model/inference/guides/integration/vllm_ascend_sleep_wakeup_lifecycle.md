---
type: Guide
title: vLLM Ascend Sleep 生命周期：权重、KV、通信组与图重捕获
description: 按Sleep/Wake阶段核对权重、KV与GlobalTE缓冲区注册，识别部分失败、storage合并/配置范围和Store所有者边界，再验收通信与图恢复。
tags:
- task.implementation
- topic.memory
- topic.reinforcement_learning
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/sleep_mode.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/sleep_mode.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device_allocator/camem.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device_allocator/sleep_mem_optimized.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/camem_allocator.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/mooncake_transfer_engine.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/kv_transfer/test_mooncake_transfer_engine.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/utils/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/base_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_layerwise_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_hybrid_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_d2rh_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_backend.py
  role: implementation
created_at: '2026-10-29T09:42:28Z'
updated_at: '2026-10-30T05:08:15Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Sleep 生命周期：权重、KV、通信组与图重捕获

## 范围和资源模型

enable_sleep_mode对所述池分配进行管理；固定Worker实际使用weights/kv_cache，文档overview的weight单数不是阶段API标签。Level1 把权重移到 CPU、丢弃 KV，需要足够 host RAM；Level2 丢弃两者，必须重新加载或更新权重。sleep 只保证该 allocator 管理的资源，不等于进程所有 HBM 清零。

按版本安装与 worker spawn 前提准备，不能把来源针对旧版本的 COMPILE_CUSTOM_KERNELS 说明当成所有当前 wheel 自动具有低层 allocator。比较真实平台支持、free HBM 与 allocator 记录，避免从其他进程占用推断泄漏。

## 额外清理与恢复顺序

仅 rl_config.enabled=true 下启用 sleep_mode_extra_cleanup。它清 ACL graph Attention workspace、使捕获失效并重置 graph manager；等待 pending PP send、同步设备后销毁 HCCL 组。固定Worker wake先处理allocator、transfer buffer与保留参数/buffer，再进入额外manager恢复HCCL、刷新MoE runtime并按阶段重捕图；文档概述顺序不能直接当作这条源码调用顺序。

Level2 按 `wake_up(tags=["weights"])`→所有 worker 加载/转移新权重→`wake_up(tags=["kv_cache"])`。extra cleanup 下仅 tags=None 或包含 kv_cache 才重捕获，避免权重尚未准备时提前捕图。旧顶层 enable_sleep_mode_extra_cleanup 已移除。

## 控制与验收

在线接口需开发端点；sleep level 取 query string，JSON body 不生效。停止发新请求并核对生命周期状态后操作。记录每阶段 HBM/CPU、通信组恢复、graph capture、首请求与稳态时延，Level1 固定输入比较输出；Level2 确认实际新权重版本后再恢复生成。

额外清理以更慢 wake 换更低 sleep HBM，不能只测 sleep 峰值忽略重捕获时延。关闭 extra cleanup 回退资源策略；Level2 丢掉的权重内容不能靠关开关恢复，必须重载。失败保持暂停或重建已知环境。本次未执行真实 sleep/wake。


## 平台证据待补

主指南没有整项sleep/extra-cleanup硬件表；hardware_profile.py也没有sleep能力位，通用设备档案不能证明该生命周期全链路。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 固定实现的三个消费入口

按[CaMem接入与内容状态](vllm_ascend_camem_allocator_lifecycle.md)核对实际weights/kv_cache、自定义tag、CPU备份、选择性wake和逻辑usage；按[映射/回调失败](../../runbooks/runtime/vllm_ascend_camem_mapping_callback_failure.md)保留VA/physical/CANN错误阶段，不能用is_asleep或条目删除代表完整资源退役。

HCCL anchor、共享组refcount、MoE stale/update_group与分阶段ACL capture见[HCCL/图恢复](vllm_ascend_sleep_hccl_graph_recovery.md)。该Host实现会在单rank或准备失败时跳过HCCL清理；“额外清理开启”不代表每周期都销毁了所有通信组，也不扩大已有平台支持证据。

sleep_mode.po的26条有效非空译文已全文与当前英文对照，0obsolete/fuzzy且msgid均匹配。中文trade-off措辞应结合上下文理解为释放更多sleep-time显存而增加wake/recapture延迟，不能反推收益方向或固定节省量。旧weight单数、概述wake顺序与固定实现的差异按上述卡片保留；未运行生成器、线上HTML或NPU。


## Mooncake缓冲区注册的本地状态

固定实现的`GlobalTE`由`global_te`实例持有缓存engine、`is_register_buffer`和`registered_buffers`，初始化锁与注册锁分开。初始化只在native initialize返回0后发布engine；成功后再次get不会按新的hostname/device参数重建。首次失败的重试guard与缺包边界见[FAQ诊断](../bringup/vllm_ascend_faq_diagnostic_boundaries.md)。本节核对Python Host控制和选定调用点，未验证Mooncake SDK、CANN、通信inflight或完整并发安全。

| 操作 | 成功后的本地状态 | 中途失败与消费边界 |
|---|---|---|
| `register_buffer(ptrs, sizes)` | 持注册锁，要求engine已初始化；逐项register_memory成功后才记录完整zip列表并置True | 原来为True就直接返回，新的地址/大小不会自动追加或替换。某项失败时，此方法没有记录/回滚本轮已成功前缀，不能只据False判断SDK没有已注册区域 |
| `unregister_buffer()` | 先disconnect_all_peers，再逐地址unregister_memory，全部成功才置False；保留原列表与engine | peer断连失败时不继续注销；某地址失败时已处理前缀不自动重注册，标志仍True、列表仍完整。True不能证明各地址仍全部注册 |
| `reregister_buffer()` | 在False且有保留列表时逐项注册，全部成功才置True | 中途失败保留False和原列表，无前缀回滚。下一次按全列表重试会触及已成功前缀，SDK重复注册语义在本次范围外 |

`registered_buffers`是整数地址/长度列表，不持有tensor存储所有权；flags也不是设备注册状态的实时查询。公开`disconnect_all_peers()`取得注册锁，私有版本供已持锁的注销路径使用；初始化前调用断连是noop，单独断连不清注册标志。一次成功的engine初始化、一次清晰日志或锁内方法返回，都不证明整个KV传输生命周期已完成。

辅助方法直接以`zip(ptrs, sizes)`遍历，自己不检查两列表等长；直接传空列表可置True并留下空列表，后续注销/reregister的空列表guard直接返回。这是该helper的局部边界，不代表已配置的正常KV路径允许空缓存：下述configured collector会拒绝没有可注册tensor的配置。判断输入是否能到达，必须沿具体调用者核对，不能凭helper单点推断全链路缺陷或实际泄漏。

## Worker的Sleep/Wake注册顺序

Worker先同步、保存Level2所需参数/buffer，按条件执行额外manager.sleep，再同步，随后`global_te.unregister_buffer()`，成功后才调用allocator.sleep。GlobalTE注销不依赖extra-cleanup开关；此处失败会阻止后续allocator.sleep，但前面的额外清理可能已经发生，不能假设失败后整个Worker仍处于sleep之前状态。

wake先经过NZ模式检查，再allocator.wake_up；只有`tags is None`或包含`kv_cache`才`reregister_buffer()`。仅`weights`阶段不会重注册KV。随后按weights阶段恢复保留参数/buffer、进入可选manager.wakeup并最终同步。因此“weights醒来”或allocator已映射并不是KV传输可用信号；重注册失败也不自动撤回已经恢复的allocator映射。

保留整数地址要求实际backing仍有有效所有者、VA及长度与重映射相容。CaMem逻辑状态、真实映射、SDK注册、peer关系、HCCL及图捕获应分别核对。不能通过手动翻转`is_register_buffer`、清空列表或直接循环重试来宣告恢复成功。

## 注册范围与逻辑KV地址分开

`collect_storage_merged_register_regions`递归读取tensor/list/tuple/dict并跳过空tensor；同一storage仅作为归组key，不能直接用raw storage地址替代实际注册起点。实际view的`tensor.data_ptr()`计入offset，接触跨度按element_size加各维`(size-1)*stride*element_size`求和，而非只取逻辑nbytes。此处没有证明任意负stride、损坏shape或未知tensor子类都有效。

每个storage内部排序并合并相交或间隔不超过`REGISTER_MERGE_GAP_BYTES=4096`字节的范围，不跨storage合并；覆盖间隙使registered_bytes可以大于逻辑payload。metadata继续使用每个逻辑tensor自己的地址、block/stride信息，不能把合并后的注册起点当每层的传输地址。该4096阈值也不是EPLB/HIXL分段参数。

`collect_configured_register_regions`则按KVCacheConfig backing归组：单storage尝试从raw base向上按`KV_CACHE_BUFFER_ALIGNMENT=2 MiB`对齐，以配置size形成范围，只有它在allocation内且所有实际view跨度都装得下才采用。否则退回实际view最小起点到storage末尾；多个独立storage分别处理，不能把整份配置size应用到每个独立分量。非法范围或无可注册tensor会抛ValueError，不能伪造空tensor绕过。

两个collector的同名统计字段不完全同义：storage-merged的logical_tensor_count/bytes累加实际非空tensor及nbytes；configured版本统计配置tensor并以注册长度和填写logical_total_bytes。比较碎片化和内存开销前记录collector类型，不能直接用同名“logical”数值计算压缩率。

`validate_register_region_count`只限制`len(ptrs) <= MAX_HCCL_REGISTER_REGIONS=256`，超限报错带registered_bytes及可用逻辑统计。它不是所有地址、ptr/length配对、对齐、单区长度、SDK有效性或全硬件HCCL能力的验证。先弄清实际collector和调用路径，再考虑减少碎片或合法合并，不能只抬高常量、强行跨allocation合并或吞掉注册错误。

## 连接器调用路径决定注册所有者

选定片段中，base_worker使用configured collector；普通MooncakeConnector及Layerwise区分其hybrid分支和storage-merged分支，构造范围、计数校验后进入GlobalTE。HybridConnector还构造共享页及分量offset，其use_hybrid分支调用configured collector和校验；不能把该分支内校验推成所有分支共同执行。D2RH在取得自身范围后校验并注册。这里仅覆盖各注册调用点，未覆盖整份connector、布局、请求协议或所有发送完成条件。

AscendStore的MooncakeBackend还分所有者：`_use_store_independent_te`或`_prefetch_conf.use_dict_setup`时逐区调用`store.register_buffer`，选定方法仅对非零返回记录error；否则仅在`not self._use_fabric_mem`时取得global engine并用GlobalTE注册，fabric分支不走这个global注册。不能把这个局部日志分支推成整份Store调用链都忽略失败，也不能据Worker的GlobalTE清理推断Store/native独立持有的所有区域都已注销。

## Agent诊断产物与停止条件

记录rank/进程、engine owner与collector、原始ptr/length列表及配置、实际backing所有者、sleep级别与tags、每阶段最后成功SDK调用/返回码、当前flag与保留列表、peer及allocator/HCCL/图阶段。部分失败后暂停新请求并保持可审计现场，按已确认的SDK清理/进程重建方案恢复；不要假定重复native调用幂等或所有前缀都已自动回滚。

固定UT文件用MagicMock和可选module替身定义了并发getter仅获取初始化完engine、native初始化/构造失败后不重试、注册前置条件/重复调用、注销→断连→重注册、部分注销失败和断连失败顺序。本次只读取测试定义，未执行；该文件没有给出空输入、两列表不等长和首次部分注册的全部覆盖，也不能据此推断整个上游测试集没有覆盖。

验收仍需目标版本/硬件上的逐阶段资源观测、真实传输、sleep/wake后首请求和固定输入结果，Level2另核实际新权重。未取得这些结果前，本卡保持draft/空平台，不把静态调用关系、UT定义、内存统计或本地标志当NPU/Agent成功。
