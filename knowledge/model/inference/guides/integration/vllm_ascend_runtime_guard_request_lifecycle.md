---
type: Guide
title: vLLM Ascend Runtime Guard 请求生命周期：波次、异步IO与延迟回收
description: 沿 RequestGuardStore、WaveTracker、RequestIoSnapshotManager和ActionQueue解释请求结束、D2H裁剪、同波去重、后台检测/报告与8波回收上限，识别缺证据、缓存复用和队列丢弃。
tags:
- task.debugging
- task.design
- topic.kv_cache
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/io.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/hooks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/queue.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/rank_gate.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/actions.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/_defaults.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/async_utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/dist.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/bus_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/dump.py
  role: implementation
created_at: '2026-10-29T18:52:32Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T19:31:47Z'
---

# vLLM Ascend Runtime Guard 请求生命周期：波次、异步IO与延迟回收


## 范围与所有权

固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，并对照原生vLLM v0.32.0的AsyncOutput接口。标准MRv2的Host状态与观测接线，没有整项硬件集合，保持draft/空平台。bus与Host dump/持久化链已由后续专卡补充；外部设备event、特殊布局/映射及实际NPU结果仍未闭合。

RuntimeGuardProcessor.bind维护每进程单例，一进程应最多绑定一个runner；Store也是进程级单例。I/O manager不是第二个请求状态所有者，主要负责Store累计数据和同wave快照缓存。rebind只重指向部分现有组件，不等于新建并清空所有状态/配额/队列；换模型时不能把bind当作完整reset。

## 三个时钟：执行波次、采样stamp、后台提交

WaveTracker只在allow_manual_dump=True时advance；idle/dummy的协调调用不一定增加真实wave。采样stamp是每请求受锁保护的FIFO，避免异步下波先record覆盖上波未take的stamp。check_after_sample按请求take；缺stamp会warning并退回current_wave，不能据回退值认定严格属于当前forward。

检测/报告在last-PP TP0，KV dump在last-PP所有TP；不能强迫其他TP也get_output来均摊检测，否则可能与后续TP collective失步。DP标签优先runner/config全局DP身份，不盲用external DP各自world里的group rank=0；CP标签为pcp_rank*dcp_size+dcp_rank。组信息缺失时各gate的回退不同，不将pre-init路径当作完整分布式支持。

## 标准采样顺序与异步输出

step装饰器在execute_model前sync，放在torch.inference_mode装饰器内部；idle DP的execute_dummy_batch也接相应同步。不要把sync移入每次_dummy_run，因为一个execute_model可能再调用_dummy_run而重复参加collective。

sample装饰器先窥视即将被父类清掉的input_batch/finished IDs，再临时包compute_logits（pre-grammar、一次）和postprocess_sampled。随后由processor顺序执行：sample_fn→mark_finished→可选spec检测→record sample waves→host输出可用时after-sample→end-of-wave。

use_async=True或返回AsyncModelRunnerOutput时跳过同步after-sample；V2即使同步调度也可能返回AsyncOutput。只有输出rank的AscendAsyncOutput.get_output在inner完成后调用after-sample。原生AsyncOutput先等待copy_event，再按num_sampled逐行裁去padding；在此前追加原始padded数组会夸大累计输出和重复检测。inner因NaN策略或EP故障等抛错时，后面的Guard hook并不会完成，不能用缺Guard报告证明没有数值问题。

观测hook多数由_soft_fail捕获Exception；sample_fn、accepted-count回调和涉及collective的end-of-wave不构成同样的“任意异常都可忽略”保证。尤其同步门禁有意不soft-fail，随意吞异常会造成其他rank等待。new Runner适配应逐点保持次序、rank与异常边界。

## 累计I/O与快照权威

need_io仅在token_repeat开启，或任一detector开启且save_sensitive_info=True时为真；dump-only/hot-reload-only不自动运行整个采样链。完全关闭的条件还要求热加载关闭、无检测、无dump/手动触发，hooks才直接返回原方法；这描述分支，不是已测的零开销数字。

Store保存output_token_ids，append过滤-1占位符；不自动过滤所有其他负数或验证词表范围。同wave的相邻相同chunk去重，refresh_config在需要累计IO时清frontier；跨wave相同输出仍保留。检测器还需维护消费游标，不重新给已写入的旧chunk评分。报告里的持久化长度上限不会自动裁掉Store全部累计历史。

prompt在首次prefill从scheduler_output.scheduled_new_reqs缓存，首个非空值保留，避免staged host mirror尚未提交或请求结束后索引已删。快照优先Store累计输出，否则逐层回退runner/raw request state和MRv2 staged数据；计数0可能包含“没取到数据”，不能一律解释为真实空prompt/输出。

include_token_ids=True的昂贵快照按req_id和选项缓存；计数路径不缓存，append和新wave会清相应缓存。I/O字段合并覆盖detector detail同名字段，因此最终报告的请求累计计数与检测窗口计数需区分。

_read_staged_row先接受非全0的host mirror，否则尝试device；全0被当成未materialize启发式，不是通用数值合法性检查。显式req_idx优先于ID映射，也不自动证明索引未因batch重排而过期。真实UVA与分离host/NPU副本的权威不同，见[UVA元数据合同](vllm_ascend_uva_metadata_contract.md)；缺失或过期镜像不能作为模型输出全0的根因证据。

## 请求结束不是立即销毁

mark_finished先标记finished和finish_mark_wave，保留同一对象，供最后的异步输出/检测/dump继续使用。cpu_jobs、dump_jobs和WaveTracker.pending共同延迟reap；达到内部max_deferred_waves=8时即使pin/stamp仍在也可强制回收。它是波次上限，**不是8秒的定时清理**；没有真实wave推进时不能据此承诺墙钟时间内回收。

clear清检测器私有状态、Store并运行清理hook，processor再丢stamp。最近reaped ID用最多1024项的环记忆，晚到append可被标记成finished zombie以待reap；这是有限记忆，不是永久防重放或跨进程请求epoch协议。请求ID复用和过晚输出仍需完整身份对齐。

kv_dump_allowed拒绝已reaped ID，但允许finished未reaped和部分未知ID；已有dump job消费时不重新把“还允许arm”当完成保证。KV可能已被allocator释放或复用，request_finished_at_dump必须保留，Store活着也不保证物理block仍归原请求。

## CPU队列、报告与自动配额

after-sample先追加IO并排空logits Incident，再向ActionQueue提交CPU token_repeat。请求被cpu_jobs pin；提交失败时撤pin。重任务在满队列时丢弃而不内联，轻报告可在满队列时内联，所以不能一概声称所有报告都在后台且不影响推理。队列默认64、单daemon线程；stop丢弃等待任务并最多join2秒，不证明正在运行的任务已完成或全部文件已落盘。

CPU任务读取执行时Store tail而非冻结token包，wave stamp来自入队时，积压时两者可能跨波。ReportWriter按(type,req)计写入上限，默认1；成功写至上限会停掉该请求所有detector，失败写会尝试回滚最新一次计数。更高上限还有64波起、逐次翻倍的同pair退避，缺wave可跳过后续写。

动作入队的report dedupe key则是(report,wave,req_id)，不含incident_type；同wave同请求多种检测结果可能共享一个pending report名额。报告文件数不是所有Incident数，也不是完整检测覆盖率。dump_attempted只表示动作意图，报告的dump_dir是请求根提示，不保证某wave的.pt已存在。

DumpQuota.try_consume在锁中检查并消费，manual consume_quota=False绕过；refund仅退还自动计数并清冷却。它本身没有决定什么时候该refund，实际动作/退款路径见后续补充与专卡；不能用quota或manual水位增加证明D2H完成。

## 验收

按request、global DP/TP/PP/CP、采样stamp/arm/drain wave、IO长度、queue状态、report与实际.pt分别对齐。结束请求、无Incident、队列接收、文件存在和数值正确各需独立证据；遗漏、停检、soft-fail和超期回收均不能当作正常。未执行NPU、并发故障注入、dump或Agent A/B。


## 配置关闭与dump退款的后续生命周期

配置cascade在needs_sample_hooks由开转关时清检测侧Store/stamp和IO缓存，丢未claim的auto jobs并按arm_id退款；已经deferred的jobs仍可在本波继续D2H。它不是所有后台任务及物理KV的同步reset，框架切换/退出仍要分别核对。

DumpKvAction.prepare消费一次quota可排多个请求job；未claim丢弃或TP0 drain中整arm无snapshot时才按arm退还，异步torch.save失败不退款。cpu/dump pin随任务完成/丢弃释放，保护Store状态，不锁allocator block。完整Host动作和manual local差异已补到[dump排查卡](../../runbooks/validations/vllm_ascend_runtime_guard_dump_incomplete.md)，不能只据quota/Store仍在推断缓存或文件完整。

报告数据处理另见[报告消费卡](vllm_ascend_runtime_guard_report_artifacts.md)，配置跨波应用见[集合同步卡](vllm_ascend_runtime_guard_collective_sync.md)。仍未在本次执行NPU、实际并发事件、服务关闭/故障注入或Agent A/B。
