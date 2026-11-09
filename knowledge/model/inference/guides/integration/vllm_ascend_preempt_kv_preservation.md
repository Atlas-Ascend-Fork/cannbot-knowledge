---
type: Guide
title: vLLM Ascend Decode 抢占保存：PreemptOffload 的顺序与回退
description: 在PD Decode先D2H保存再复用HBM，结合中文与代码核对PreemptOffload的world_size字节预算、ratio/bool校验、滑窗空槽与lookahead恢复及回退。 补充全rank事件聚合、partial/hash共享、circular与Mamba Conv/SSM独立恢复及同步copy/reset边界。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/preempt_offload_connector.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/preempt_offload_connector.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/preempt_offload/preempt_offload_connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/parallel.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/preempt_offload/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/preempt_offload/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/kv_transfer/kv_pool/kv_offload/preempt_offload/metadata.py
  role: implementation
created_at: '2026-10-29T09:45:39Z'
updated_at: '2026-11-03T05:05:17Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      phase:
      - decode
aliases:
- PreemptOffloadScheduler
- PreemptOffloadWorker
- PreemptedRequestState
- MambaConvLoadMeta
---

# vLLM Ascend Decode 抢占保存：PreemptOffload 的顺序与回退

## 范围和前提

仅 PD 解耦 Decode kv_consumer，需 scheduler_config.recompute_scheduler_enable=true。当前来源给出 A3 大预算配置，本卡不扩大平台。普通服务/PD mixed 不支持；最小 standalone connector 片段也不是混部完整方案。用 MultiConnector 保留 P/D 传输并加入 PreemptOffloadConnector。

## 正确性顺序

HBM 不足选中请求后，先建立 HBM→CPU 映射，runner 在更新 worker state 前 handle_preemptions；所有 workers 报 store complete 后才可恢复，HBM 块复用不能早于保存完成。重新调度时先分配新 HBM，建立 CPU→HBM 映射，forward 前恢复完成。

滑窗逻辑空洞必须保留，例如 [0,0,20,21] 保存仍对应原位置，只搬非零块，不能压紧列表。MTP/speculation 的 lookahead reload 要裁到实际新分配 GPU block table，不能按旧容量越界复制。

## 容量、失败和互斥

预算优先级是 cpu_bytes_to_use_per_rank > cpu_bytes_to_use/world_size > offload_host_memory_ratio×GPU块数；新部署优先每 rank 字段，按实际 world_size 核对总 RAM，不以 TP×DP 的直觉代替实现。容器 /dev/shm 需容纳 pinned tensors；来源 1024g 是特定 A3 例子，不是每服务固定最低值。

CPU 空间不足会跳过保存、回到原 recompute，不能宣称该 connector 保证永不重算。enable_offload_prefix_caching 默认 false 且实验。Qwen3.5 async 尚不完全支持，关闭异步。与 sparse Decode offload 互斥，嵌套 MultiConnector 也不能绕过。

## 验收与回退

人为压低安全测试预算触发抢占，检查 enabled/state/H2D 日志、全 rank 完成、原位置、接受数和输出，覆盖多次抢占与 CPU不足。区分基本 torch copy 的正确性目标与带宽优化。关闭 connector 恢复原重算会改变容量/时延，且 fine-grained O-proj/MLP 要求该组件，需同时回退依赖配置。本次未运行抢占测试。


## 中文预算示例与实际world_size的差异

preempt_offload_connector.po的51条译文均匹配英文，但两者都用DP2TP8、总16GiB推出每卡约8GiB。所读PreemptOffloadConnectorV1._resolve_offload_capacity实际取vllm_config.parallel_config.world_size，per-rank字段优先，否则用总bytes整除该值，不直接除data_parallel_size。

配套原生vLLM v0.32.0的ParallelConfig.__post_init__令world_size=PP×TP×PCP，external_launcher时再乘DP。在PP=PCP=1、TP8、DP2且没有后续改写时，普通分支world_size8，对总16GiB算得2GiB/rank；external_launcher分支world_size16，算得1GiB/rank。它们是所读公式下的整数例子，不是实际部署测量，也不能代替目标进程的最终值。保留构造日志role、per_rank_bytes、world_size与有效配置，不能把文档8GiB例子当此版本通则。

## 配置优先级不等于跳过校验

_resolve_offload_capacity先把offload_host_memory_ratio转float并要求正且有限，再检查cpu_bytes_to_use_per_rank、cpu_bytes_to_use/world_size。即使明确给字节预算，ratio=0、负数、NaN或Inf仍失败；“只有无bytes才用ratio算容量”不代表其他分支不验证它。有效每rank bytes也必须大于0，总值太小经整除变0会拒绝。enable_offload_prefix_caching必须是真bool，字符串false不作为正确关闭写法。

字节预算、CPU block ratio与实际物理block bytes分别留证；显式每rank16GiB是候选，不保证host容量或pinned分配成功。源码把world_size传给scheduler/worker容量路径与报告日志，不在此推导整个NPU进程/内存分配已完成。本次没有实例化这些类或执行torch分配。

## 组合部署、恢复与日志的不同含义

PD connector从P取KV；PreemptOffload在D保存被recompute抢占的已计算块，两者由MultiConnector组合。kv_load_failure_policy按指南放顶层，不塞子connector。standalone例只是D端最小片段，不开放kv_both或普通非PD场景；V1 engine也不能只凭名称推导固定ModelRunner代际。

保存映射、所有worker D2H完成、HBM可复用、恢复新块/H2D完成与forward按次序核对。空CPU块回退原recompute，不把enabled/state/H2D三种日志合并为“请求必定没有重算”。滑窗空槽[0,0,20,21]保持原逻辑位置，投机lookahead按实际分配表裁剪；prefix-sharing实验与inactive-prefix CPU offload另是一条策略。

指南1024g shm是特定A3大预算示例，不当所有NPU服务的统一最小值或实际RAM占用；容器共享内存、host剩余/连续分配、每rank预算和实际分配失败分别观察。示例JSON片段带尾逗号，先经目标参数解析核对有效结构，不把展示命令当已执行验收。Qwen3.5 async限制、与Sparse Decode互斥及原回退边界保持，本批未启动容器、调整内存或压测抢占。


## 当前scheduler/worker状态机与缓存组约束

完整补入 ceac1a2 的 manager.py、worker.py、metadata.py，未执行抢占/NPU。scheduler明确assert DCP=PCP=1；不是仅在文档中未提及CP，而是该构造有实际拒绝。CPU配置保留层/块stride、offset及groups，块数至少1；worker以scheduler数量为准纠正自己的容量估算。因此显式字节预算和实际pinned分配仍需测量，不能认为任意小预算严格不超额。

PreemptedRequestState分别保存CPU块、computed tokens、store/load事件、load起点、ready/finished；尚未全worker完成时 get_num_new_matched_tokens 返回None，而非0命中。可恢复token不超过已保存computed与当前request长度；无新增可恢复token就清理状态。分配后准备H2D失败会抛错，不能静默带缺失KV进入forward。

普通完整hash块只在prefix-sharing开启、已计算完整且非circular时复用；最后partial块无hash也会保存，不能仅按hash列表搬运。一个调度步的pending hash块可在多个被抢占请求间touch共享，仍需等待首次store。CPU空闲不足预先返回False，让原recompute策略接管。滑窗在左侧补0保留逻辑索引；circular必须恰好一个非零私有块，恢复固定slot0，不能按位置增大块表。

## Mamba恢复：SSM快照与Conv偏移分别处理

Mamba保存末尾1+K个状态块，恢复根据实际接受位置挑SSM/temporal块；Conv额外从running-state块按accepted offset移历史，不能让SSM选择规则替代Conv平移。跨cache边界时只保留块内残余偏移。metadata 的 MambaConvLoadMeta 明确记录CPU/GPU块与source_offset，normal H2D仍先执行，再纠正Conv。

worker把Mamba view的ptr/shape/stride/dtype及是否Conv作为去重身份，防与普通attention或不同状态混合；Conv shape须等spec且为2D、每cache块仅一物理行。LINEAR无Conv，SHORT_CONV全部状态按Conv，MAMBA1/2/GDN仅state0；未知backend拒绝，不能以list形状猜。

Conv只恢复 width-K 行因果历史，spec工作槽不复制，避免恢复被拒绝的候选；source_offset必须非负且范围不超width。这里的K来自构造配置，动态投机变长时必须另核scheduler/worker实际预算与保存布局，不能默认每批K会同步重建所有状态。

## 保存完成、请求结束与reset的独立条件

handle_preemptions在input state更新/块清零之前同步D2H，need_flush先等未完成load；同store事件去重。start_load_kv同样以sync=True恢复，且_submit_transfer在copy前全设备synchronize，底层是逐块逐tensor torch.copy_，不是Native offload的batched DMA。non_blocking=True不代表当前完整路径无阻塞，也不能据此估算异步重叠收益。

每worker报告{store_event:1}；metadata aggregate只求和，scheduler还跨步累计，达到world_size才将对应请求ready并发布hash块。它不携带worker身份去重，调用方必须保证一次事件每rank只报告一次；重复计数不能当全部ranks完成。空传输事件也有完成语义。H2D完成后先报告finished_recving，再释放为load临时touch的GPU块和CPU请求引用；HTTP完成但store尚未ready只标finished，等待保存闭环后才清理。

reset_cache在任何pending transfer或未闭合请求状态存在时返回False，不可用reset绕过在飞行copy。submitted/pending集合、高水位及当前metadata寿命各不相同；clear_metadata不等于取消copy。验收应覆盖共享hash/同一步双抢占、partial块、全rank完成、请求在保存前结束、reset拒绝、滑窗空洞、circular与Mamba接受跨边界，再比较原recompute输出及实际阻塞时间。本节是静态源码合同，保留原A3平台与draft/stable证据强度，不新增verified。
