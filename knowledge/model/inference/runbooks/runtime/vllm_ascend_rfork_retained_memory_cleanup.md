---
type: Runbook
title: vLLM Ascend RFork 失败排障：注册内存保留、lease回报与seed退役
description: 按 RForkTransferBackend、RForkSession 的注册与退役合同排查 fallback 拒绝、内存保留和 seed
  不可发现，区分 READY、DEFERRED、SERVING、未决 lease、owner 与降频重试。
tags:
- task.debugging
- task.implementation
- topic.memory
- topic.checkpointing
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/transfer_backend.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/session.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/planner_client.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/seed_server.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/seed_client.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/types.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/manifest.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/tensor_layout.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_loader/rfork/rfork_loader.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/rfork/rfork_planner.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_lease_release.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_restored_lifecycle.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_registration_cache_isolated.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_transfer_timing_isolated.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_session_server_integration.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/test_rfork_planner.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/conftest.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/rfork_test_support.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/model_loader/rfork/session_test_utils.py
  role: supporting
created_at: '2026-10-29T20:37:39Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T03:05:17Z'
---

# vLLM Ascend RFork 失败排障：注册内存保留、lease回报与seed退役

7d9e增加主机Engram释放与共享owner保护，迁移清理路径前读[7d9e运行时差异](../../guides/integration/vllm_ascend_7d9e_runtime_delta_contract.md)的RFork节；不能在MR清理失败后先分配第二模型，也不能由draft释放target持有的表。


## 触发与范围

RFork报fallback aborted、memory remains registered、source lease unresolved、seed不可发现、HTTP removal失败，或看似加载完成却不能释放NPU内存。固定Ascend ceac及其所需原生vLLM v0.32.0；硬件整项集合未知，保持draft/空平台。本次只阅读实现/测试定义，未初始化TransferEngine、绑定端口、注册内存、复现故障或运行NPU。

## 先分清三个资源与三个成功条件

RForkTransferBackend持有原生engine、注册地址、tensor和原始storage owner；RForkSession管理lease、HTTP seed handle和线程；planner管理可分配seed与容量。模型可推理、planner已接收广告、MR/engine可退役是不同条件。state=SERVING或loader completed不等于所有planner请求已确认，删除一条广告也不证明外部原生read均已结束。

engine懒初始化要求YuanRong TransferEngine/MemoryRegistration/ErrorCode APIs，initialize使用port0、ascend、当前npu设备，再读回get_rpc_port组成session。缺API或返回错误可让RFork走已定义回退；强行填HTTP seed端口不能替代engine真实RPC地址。固定源码未给出本次已安装/验证的SDK版本，部分早期失败只有best-effort finalize，不能宣称任何初始化异常都完整退役。

## 注册的是logical范围及其backing，不是payload扩大许可

_select_weight_blocks从NPU allocator snapshot的active_allocated块选择与tensor有效范围重叠的块，合并相邻/重叠backing，扣除target共享区域。每条tensor范围必须完整落在可用backing中；多个logical范围可在同backing内合并，再以MemoryRegistration(logical_start,logical_size,backing_start,backing_size)分批注册，每批最多4096项。

register_memory_region保存命名tensor、NPU format、原始storage owner及provisional manifest，再在每次batch前记录所有attempted addresses。即使只部分成功或抛异常，也不能按“未成功返回”丢弃owner。回滚未确认时保留注册状态给后续重试；仅把Python model设None或执行empty_cache不足以安全退役。

register拒绝空清单、重复/空名字及named parameter/buffer中的实际非NPU状态；发现/共享/manifest条件见[兼容身份指南](../../guides/integration/vllm_ascend_rfork_manifest_contract.md)。snapshot_registered_weight_blocks返回副本不pin寿命，draft排除地址需要target storage持续存活。

## read可能已写入部分权重

read前先验manifest、按seed shape尝试view并重验dense，再按name构造双方指针与numel*element_size。iter_transfer_chunks将大tensor分段，每chunk至多1GiB、512段；不因allocator/NZ backing更大就扩payload，也不只按地址合并不同名字。

batch_transfer_sync_read逐chunk顺序执行，后续失败不会自动回滚早先已写入的内容。不能把半成品返回推理或直接重用为seed；先按session清理门禁恢复default加载。函数名带sync/成功result是外部API合同，不是本次NPU完成性证据。

日志throughput=总逻辑GiB/read阶段耗时，不含完整初始化、注册、metadata、lease、post-load与发布。TP0用INFO、其他rank可DEBUG；日志缺失/一rank带宽不能替代全部rank成功、质量和服务ready时间。

## unregistration和finalize的重试边界

_unregister_weight_blocks对registered_memory_addresses去重、分批；成功批次从待处理列表删除。kNotFound批错误可能只处理到首个不存在地址，于是逐地址确认，已不存在可视为完成，其他错误保留未确认地址。只有确认全无后才清manifest/tensor/storage owners；不从单个batch错误推导所有区域都已解除。

finalize_transfer_engine默认最多10次、间隔1秒，仅kNotReady走该重试；异常、其他错误或耗尽返回False，保留engine与owner状态供受控重试。成功才清注册状态/session/engine和初始化标志。这里的最大10次与lease release的fast attempt阈值不是同一个策略。

## lease释放是后台流程，阈值不是硬停止次数

register_destination先设CLEANUP_REQUIRED，注册并绑定结构digest后REGISTERED；acquire_seed才LEASED，并起TTL/3、夹在0.1–30秒的renew线程。renew失败会记录但不自动证明lease仍有效，也不由日志保证长read不会超过远端TTL。

read成功变TRANSFERRED并启动release worker，HTTP在_lock外执行。put_seed200/404视为RELEASED；404只表示远端已不存在，不证明及时释放。408/429/5xx或网络异常为RETRYABLE；其他拒绝保留未解决lease并停止发布。

lease_release_max_attempts默认3，是快速重试预算；RETRYABLE超过后仍继续，间隔至少60秒。REJECTED/工作线程无法启动可标exhausted，阻止seed promotion；不是每种失败都每隔固定时间无限重试。transfer完成、lease ack、seed可发布分别取证，不能把release请求发出当作ack。

start_seed_service可在READY保存model引用并返回DEFERRED，等release确认再promote；已可推理的模型不必等planner释放网络往返。prepare_for_fallback的can_schedule_seed只要求service_stopped与memory_reset，lease_released可False；若两项不满足，loader拒绝再分配第二模型，详见[加载接线](../../guides/integration/vllm_ascend_rfork_processed_weight_loading.md)。

## 发布、撤回、锁和关闭次序

_seed_lifecycle_lock须先于_lock，串行seed start/stop；health、广告/删除网络操作尽量在状态_lock外，但native read由_lock覆盖以防并发unregister。不能把“不持状态锁”当成所有调用都无阻塞。

seed服务先绑定真实socket并做带key健康检查，再report。端口base按base+2*global_rank+draft_slot，超范围或配置端口EADDRINUSE可回OS端口；其他bind错误不统一静默降级。启动资源在queue交接前发布，超时/health失败仍保留live handle供清理，不只看thread已请求stop。

首次广告RETRYABLE可已SERVING但pending，heartbeat继续重试；永久拒绝或HTTP线程死亡会撤回广告，保留handle/MR待正常清理，不主动让半退役资源重新注册。planner.last_advertisement在发请求前保留，响应丢失仍有撤回身份。结构digest发布检查的bool返回边界见[manifest指南](../../guides/integration/vllm_ascend_rfork_manifest_contract.md)。

_stop_seed_service先停/有界join heartbeat，再请求remove_seed，确认后stop HTTP handle，成功才清handle。remove失败会保留本地服务和内存；_reset_transfer_locked拒绝在仍拥有seed_server时unregister。Requests timeout是网络操作的超时参数，不应解释为全流程严格总时限。

shutdown先发stop给release/renew并串行清理service；只有service清理成功且source lease本地已无未决，才finalize engine，成功才FINALIZED并取消atexit。它不新发阻塞release请求；已在途ack仍可能完成。planner TTL回收的是远端容量，不会自动把本地seed_lease清空或证明MR释放。重入保护、失败保留与后续受控retry要按实际state/owner核对。

## example mock planner只提供协议参考

examples/rfork/rfork_planner.py是单进程内存Store/RLock，默认seed heartbeat TTL和独立lease TTL均60秒，GC sweep5秒。heartbeat不renew已有lease；renew_seed_lease另更新leased_at；过期/重复release不重复返还容量。remove或心跳过期先draining、停止新分配，仍有active lease时remove返回409，直到release/TTL后可删除；不能看到409就直接关闭MR。

SEED_REFCNT=0只是heartbeat字段，容量取planner配置；标为fifo的选择实际按最旧heartbeat时间和identity，lru按分配recency，不能当持久全局入队顺序。Store默认wall clock、非HA持久协议，本次未运行；它的默认值和回收策略不自动代表任意外部planner。

## 取证、验收与停止条件

保留原始错误、rank/主草稿、engine/peer session、key/digest、layout、attempted/confirmed/remaining addresses、storage owner、bytes/chunk、lease的脱敏关联和HTTP/state时间线。清理失败、服务仍可访问、lease未决或native结果不明时，不宣称已释放/可重新发布。

已读测试定义覆盖release分类/降频后恢复、未决shutdown、全局恢复、alias/scratch排除、布局诊断与部分真实HTTP listener组合；native/backend/planner仍多处注入mock。它们未在本次执行，不替代真实SDK/NPU、并发read退役、模型输出及性能A/B。
