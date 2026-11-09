---
type: Guide
title: vLLM Ascend Sleep 恢复：HCCL锚点、共享组引用与ACL图阶段
description: 沿 SleepWakeupManager、HcclSleepWakeupManager 与 HcclPgRegistry 核对 PP drain、锚点barrier、共享组退役、MoE
  stale/update_group 和选择性ACL重捕获，区分计数与物理资源。 说明 rank 顺序与 hccl_config 配置如何进入共享组键，并保留串行创建和最后
  owner 释放的约束。
tags:
- task.implementation
- task.debugging
- topic.memory
- topic.parallelism
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device_allocator/sleep_mem_optimized.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_distributed.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/_hccl_pg_registry.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/moe_comm_method.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/fused_moe/token_dispatcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/device_communicators/npu_communicator.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/device_communicators/base_device_communicator.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device_allocator/test_sleep_mem_optimized.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/sleep_mode.md
  role: supporting
created_at: '2026-10-29T21:37:30Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-30T18:37:27Z'
aliases:
- HcclPgRegistry
---

# vLLM Ascend Sleep 恢复：HCCL锚点、共享组引用与ACL图阶段


## 任务与证据范围

RL暂停后显存未明显下降、分阶段wake后通信/图未恢复、MC2继续使用旧communicator，或把Destroyed N组日志当物理释放数。固定Ascend ceac与必要原生v0.32接口；整项平台未知，保持draft/空平台。这是Host控制/调用知识，不是所有CANN通信、图、模型/硬件的实测闭包。

## 入口顺序与各自的资源

仅rl_config.enabled与sleep_mode_extra_cleanup均真才进入额外清理。Worker在基础sleep中先处理内容保留、调用manager，再同步并unregister transfer buffer、执行allocator.sleep。额外manager.sleep在use_aclgraph时先清图工作区/缓存，再等待pending PP sends、同步NPU并处理HCCL；这里的HBM差值不是纯allocator回收量。

固定Worker wake先恢复[allocator映射/备份](vllm_ascend_camem_allocator_lifecycle.md)，按KV tag重注册transfer buffer并按weights tag恢复保存参数/buffer，然后manager.wakeup。manager内部顺序是HCCL→dispatcher→MoE runtime→按需图重捕获→释放临时锚点，Worker最后同步设备。不能把manager内部顺序推成HCCL总在allocator之前恢复。

## 图清理只处理规定状态

AclGraphSleepWakeupManager处理target、draft与draft-prefill三组graph params：attention workspace逐项置None；dataclass中MutableMapping的list值重置为空list，非list元数据不被同一循环清空。已注册wrapper的concrete_aclgraph_entries清除、first_run_finished=False；model_runner graph manager有对应属性时清graphs/_graphs_captured。

不是任意私有图对象、外部内存或所有模型执行态都被通用清理。wakeup(tags)在非None且无kv_cache时直接不capture；其余在当前VllmConfig上下文调用capture_model。weights先醒、外部reload尚未完成时不应提前据“已wake”恢复生成。

## HCCL lifecycle anchor需要真实初始化

iter_alive_group_coordinators从弱引用注册表快照取活对象并按id去重。destroy_hccl先保存业务coordinator列表，再_ensure_lifecycle_anchor：world_size<=1返回False；多rank创建覆盖world ranks、use_device_communicator=False、group_name=sleep_lifecycle_anchor的coordinator，并对device_group执行NPU barrier，不能只以lazy new_group返回当实体已存在。

锚点对象跨周期保留，下一周期必要时restore_hccl再barrier。锚点初始化失败，或prepare_moe_hccl_teardown抛错，manager标_skip_hccl_cleanup_for_cycle并跳过该周期的业务HCCL清理；相应restore分支重置skip而不重建业务组。失败路径不保证各rank已自动达成相同状态，需目标分布式取证。

每业务group调用destroy_hccl，保留anchor；wake时恢复业务device group并重新构造需要的NPUCommunicator。仅tags=None或含kv_cache时，在图重捕获后对anchor barrier并destroy其HCCL；只醒weights会保持锚点，避免阶段间控制面提前退役。barrier/restore/capture失败可留下部分状态，代码不是全流程原子事务。

## 共享注册表与物理销毁口径

GroupCoordinatorPatch通过HcclPgRegistry取得device group，同时创建/保留Gloo CPU group。HcclPgKey含backend、顺序敏感ranks tuple、经规范化的hccl_config和reuse_domain；未知非默认选项或不匹配global_ranks使该配置不复用。Key不是任意对象完整序列化，未承诺所有未知/循环/不可hash配置都优雅回退。

_resolve_reuse_domain给eplb相关组或mc2专门域，其他用shared。create_hccl_pg_options又把group_name写入被审阅的hccl_config；它不同于被忽略的顶层group_name字段。相同rank集合或shared域不代表key相同；anchor还有hccl_buffer_size=1配置，不仅靠名字推断资源共享。

registry acquire仅对lookup/refcount加锁，create_fn在锁外；调用者仍须进程串行、各rank全局有序创建collective，不能当并发PG工厂。release在最后owner才destroy物理group，非成员sentinel不销毁；clear只清metadata，依赖外层分布式环境已负责退役。最后release先删entry再实际destroy，失败路径并无统一回滚保证。

coordinator._release_hccl_resources的布尔值还可能反映device communicator对象/存在的空key列表，并不等于一个physical HCCL communicator已消失。当前NPUCommunicator继承的原生DeviceCommunicatorBase.destroy为pass；实际process-group退役仍沿registry/句柄追踪。Destroyed/Restored数量、coordinator数量、物理group与释放HBM分别看。

## MC2 dispatcher与MegaMoe runtime

Hccl manager先按已注册_MoECommMethods的token_dispatcher刷新HCCL group信息，再调用可用refresh_hccl_runtime_state。TokenDispatcherWithMC2.refresh_hccl_group重新读取恢复后的backend communicator name；不是任意所有模型/dispatcher私有缓存的自动修复。

已读FusedMC2CommImpl.prepare_hccl_teardown在有symm buffer时检查_ctx_manager.update_group可调用，否则拒绝退役；将_mega_moe_hccl_state_stale置True。刷新时在torch.inference_mode下update_group，更新buffer的group/rank/name/world_size/ccl_buffer_size，对恢复MC2组barrier后才清stale。

缺外部cann_ops_transformer接口、update/barrier失败或stale未清，都不能由“组已restore”推成runtime可用。这里只读所述Host方法，不宣称MegaMoe Device算子、全部ABI、全部量化/多模型共享状态已验证。

## 验收和剩余工作

按rank记录sleep入口、PP work完成、各graph对象、anchor/业务组key与refcount、物理句柄、MoE stale/refresh、allocator/权重阶段、图capture与首请求。比较真实HBM及sleep/wake/重捕获/稳态延迟，不用单个Destroyed日志或逻辑usage证明全部释放或收益。

380行额外清理UT定义覆盖list-only graph reset、单rank/失败skip、anchor创建/复用/barrier、准备→退役、刷新次序及KV阶段后release；本次未运行。外部PG/CANN、通信inflight、运行态刷新、完整Runner/模型和NPU结果继续待验证。
