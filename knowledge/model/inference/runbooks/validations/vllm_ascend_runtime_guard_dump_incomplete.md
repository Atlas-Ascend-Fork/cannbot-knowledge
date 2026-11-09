---
type: Runbook
title: vLLM Ascend KV dump 不完整：arm、D2H、后台保存与缓存归因
description: 追踪 DumpKvAction、KvCacheReader 和 _run_kv_dumps，排查有dumped日志却缺.pt、配额退款、manual水位与分片错层，核对block_ids、布局、K/V部件和异步保存。
tags:
- task.debugging
- task.testing
- topic.kv_cache
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/dump.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/actions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/queue.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/rank_gate.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/_defaults.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_attn_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_bind_kv_cache.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/attn_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/fa3_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/mla_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/sfa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v41.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/model_runner.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/attn_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/utils.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/utils.py
  role: implementation
created_at: '2026-10-29T19:31:47Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T19:41:59Z'
---

# vLLM Ascend KV dump 不完整：arm、D2H、后台保存与缓存归因


## 触发与证据强度

Runtime Guard已有report/request_info或dumped日志，却缺目标.pt、只有部分层/TP、manual已done但没有数据，或用dump错误定位模型KV。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，对照原生vLLM v0.32.0的所需Host接口；不是两个提交所有二进制组合已兼容的保证。标准MRv2接线，整项硬件集合未知，保持draft/空平台。

此卡闭合所列Host arm/claim/D2H调用/保存与元数据路径；没有执行torch、NPU、异常注入、文件导出或性能测试，也不替代attention/cache Device算子的完整知识。

## 按阶段确认，不合并完成信号

| 阶段 | 源码动作 | 仍未证明的事实 |
| --- | --- | --- |
| Incident/report | report的dump_attempted由动作列表决定，manual报告也可置True | 未必通过free-space/quota/queue门禁 |
| DumpKvAction.prepare | 解析目标、估算、消费一次quota、冻结block_ids并queue job | 没有在prepare做实际D2H |
| arm metadata commit | 后台写request_info或dump_skipped | .pt未必存在，request_info是arm时证据 |
| 下一wave-head claim | auto job经merged bus或TP单lane进入deferred | 提交与接收不等于读取完成 |
| end-of-wave _run_kv_dumps | 按层_slice_blocks、detach().cpu()产生KvDumpSnapshot | 尚未保证磁盘文件已保存 |
| submit_heavy / write_snapshots | 将CPU快照排队，随后torch.save | 入队可丢，部分save可失败；无跨rank完成事务 |

DumpKvPrepared只携带skip/request_infos等arm侧文件payload，commit据它写入元数据；它不代表已经得到CPU KV张量，实际CPU payload是后续KvDumpSnapshot。

auto detector dump通常是arm+1 wave；manual local由各last-PP TP在end-of-wave直接枚举本地请求并读回，无dump-job广播。覆盖仅last PP×all TP，不能称整个PP模型的完整缓存。跨rank收集需按同一incident/request/arm wave/global DP/TP/PP/CP对齐，不凭目录时间猜同一轮。

## 配额按arm，不按目标或文件

DumpKvAction.prepare默认request scope，all_requests逐目标解析block ids，manual触发忽略配置scope。自动路径空目标/全部空block会skip；需要延后解析的manual queue路径可保留空ids。估算把单rankpayload乘TP size，加内部5GiB headroom；free_bytes_at无法探测返回None或估算未知时不会仅因此拒绝。它是当时的估算，非空间预留，也不完整计算序列化开销或各rank不同文件系统。

一次try_consume可arm多个目标，共用arm_id；queue按(wave,req_id)去重，不含incident_type。没有新queue目标或prepare异常会退款；未执行就丢弃的arms及TP0 drain中完全没有快照的arms按arm退款。只要一个目标产生快照，其他目标失败不保证该arm退款；后来的异步torch.save失败也不退款。dump_count/cooldown不是成功.pt文件计数。

标准manual local路径直接_run_kv_dumps，绕过DumpKvAction.prepare的自动quota与free-space估算门禁；仍受真实数据、rank和后台保存条件约束。done在已armed尝试后推进，不要求每目标文件成功。不能用水位已到N或无配额消耗证明手动产物完整。

## 有dumped日志仍可能没有.pt

_run_kv_dumps在yield一个CPU snapshot后先produced+=1，再调用ActionExecutor.submit_heavy。submit_heavy返回None，重队列满/停止时仅warning并丢任务；调用者不会因此把produced改回0。随后arm可被标ok并打印dumped，但文件还没有写入。不能据此声称D2H与落盘都成功。

write_snapshots逐文件torch.save，失败只记异常并尝试torch_save_failed的dump_skipped.json，其他层可继续存在。marker本身写失败也只warning；无marker不证明成功。empty_block_ids、no_tensors、d2h_failed等drain marker与已有request_info/部分.pt可共存，同路径marker还可能被后来原因覆盖。

保存没有本卡可证明的临时文件replace/fsync/全rank提交协议；文件存在或非空不等于可解析、完整或属于本次运行。不要由done、日志、目录、quota或单个.pt直接恢复“已全量抓到KV”的结论。此处不提供本次未执行的加载成功记录。

## block_ids与实际缓存布局

block_ids_for_request优先runner.requests中的block_ids，再按batch索引/表、MRv2 idx_mapping、req_states与持久block_tables回退，默认kv_cache_group=0。显式req_idx并不验证请求身份；V2 device表回读还可能同步。arm冻结的ids优先于drain时live表，保护的是数值快照，不保护allocator对这些block的所有权。

Reader对runner.kv_caches中的所有层/部件复用传入的一份ids。异构cache groups、不同manager/kernel block大小、压缩/滑窗/circular缓存、量化scale及layerwise零stride别名要逐路径核对；group0的逻辑block号不能自动套到所有物理视图。

_slice_blocks在ndim>=2时把dim0当num_blocks，只保留范围内ids，按实际used_ids写metadata；越界id可被静默排除，重复id也未统一去重。ndim<2则整tensor回CPU并沿用传入ids，并非已证明逐block选择。payload.num_kv_heads取shape[-2]的启发式也不适用于任意HND/状态tensor；Agent不能按字段名直接解释物理语义。

普通attention backend的get_kv_cache_shape虽带前导2，Ascend _reshape_kv_cache_v2会拆成K/V tuple，常见部件dim0又是block，不能只凭backend shape认定Reader必错。要看最终视图shape/stride/dtype和cache spec，保留压缩、padding与kernel-block映射；当前卡没有穷尽所有特殊分支。

## 层名与K/V部件的归因风险

Ascend patch_model_runner已将runner.kv_caches扁平为K、V、scale、Conv/SSM等部件后再按device过滤，connector仍保留原始每层字典/容器。单看native原始cache.device代码就判定tuple必然初始化失败是不完整的；实际要先核对固定worker补丁的导入路线。

KvCacheReader为list构造的list_names按kv_cache_config.layer_names及extract_layer_index排序，每个list项消费一个名字，再不足时回退layer_<start+i>。若生产端一层扁平出多个tensor，名字数量/顺序不必与tensor列表一一对应；某些.pt可能被标成另一层或回退名。这是源码推导的待验证风险，不是已复现的特定模型故障。不要仅凭文件名认定哪层出错，也不要把原字典交给connector就推断Reader仍持有该字典。

必须保存源layer/component→storage view→scheduler/cache group→used_ids→snapshot文件的映射。别名层、多attention模块、插入顺序和lexicographic回退也需对齐；存在这类缺口时，dump只能作待核验线索，不能直接驱动Agent改权重、改attention公式或判根因。

## 最后核验与停止条件

finished未reaped请求仍可arm；request_finished_at_dump应保留，缓存可能已释放/复用。dump_jobs pin维持Store生命周期，不锁住物理KV；已有job的D2H尝试也不再次保证所有权。转到[请求生命周期](../../guides/integration/vllm_ascend_runtime_guard_request_lifecycle.md)核对超期回收与晚到输出。

核对每个期望请求、wave、rank和layer/component，实际文件清单、skip/warning、used_ids、shape/stride/dtype与可读性；部分成功单独列出，缺分片或映射不清时停止完整性/数值归因结论。完整模型质量仍要独立精度验收，性能仍要关闭取证后按同负载测量。报告内容解释见[报告产物](../../guides/integration/vllm_ascend_runtime_guard_report_artifacts.md)，集合同步见[配置总线](../../guides/integration/vllm_ascend_runtime_guard_collective_sync.md)。
