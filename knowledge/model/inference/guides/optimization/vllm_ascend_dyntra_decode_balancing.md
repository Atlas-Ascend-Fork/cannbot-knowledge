---
type: Guide
title: vLLM Ascend DyntraLB：单机 Decode DP 的暂停与准入均衡
description: 结合DyntraLB中文指南，按单机Decode内部DP、KV块负载和下一步计划核对准入/暂停，区分触发阈值、快照区间和保留KV，并做同负载对照。 补充planner固定cost/候选截断、KV预取和partial-tail、暂停与真实抢占、MRv1/v2输出及DP控制循环。
tags:
- task.optimization
- topic.parallelism
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/dyntra_lb.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/dyntra_lb.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/dyntra_lb_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_dyntra_lb_core.py
  role: implementation
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T05:11:27Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
      phase:
      - decode
aliases:
- DyntraLBPolicyMixin
- DyntraLBScheduler
- AsyncDyntraLBScheduler
- DyntraLBDPEngineCoreProc
---

# vLLM Ascend DyntraLB：单机 Decode DP 的暂停与准入均衡

## 范围与启动前提

DyntraLB 仅面向 PD 解耦 kv_consumer、DP>1、所有 Decode DP ranks 在单机的内部 DP。均匀长度、DP1、跨机 D DP 不在目标范围。它在原 rank 暂停或恢复请求并保留 KV，不迁移请求、不替代外部路由。

在 scheduler_config.dyntra_lb_config 设 enabled=true；不能与 enable_balance_scheduling 或 profiling_chunk_config.enabled 同开。recompute_scheduler_enable 是独立兄弟配置，两者同开选择组合 scheduler。

## 两步决策与单位

当前步执行后协调 wave/idle，收集 running 与远端 KV 已就绪的 waiting 请求，以 KV block count 估计工作量；all-gather 后规划各 rank 的 Out/In/Freeze，下一 engine step 消费。新 wave 首步没有旧计划。start_step/end_step 指产生计划的已完成快照，不能当成同一步已应用。

bubble_threshold>=1 表示绝对块差，<1 表示 (最大-平均)/最大，因此 1 不是100%。long_req_block_threshold 也以块为单位，换算 token 必须乘实际 block size。估计不包含完整模型成本或 draft 开销。

## 诊断到运行

短诊断可用 static、start_step=0、enable_diagnostics=true，确认所有 ranks 同步进入采集、无持续 KV 等待，查看 rank0 的 Out/In/Freeze。性能测试关闭 diagnostics。dynamic 是来源建议的运行模式：新请求块数超过阈值才激活，连续 dynamic_max_step 无新长请求后停用，仍受 start/end 区间控制。

阈值太小可频繁暂停，太大则不触发。保持模型、输入、采样、并发和 PD 拓扑一致，比较 DP bubble、完成率、吞吐及等待尾部；投机或异步调度需额外做精确版本组合验收。关闭 enabled 回退，不能以 planner 日志存在替代吞吐收益。本次未运行 NPU 对照。


## 平台证据待补

完整主指南限定单机内部DP Decode，没有A2/A3/950整项功能范围；单机/DP条件不能替代产品支持证据。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 中文DyntraLB：触发、快照区间与暂停状态

dyntra_lb.po的52条译文对应当前英文。单节点内部Decode DP>1和kv_consumer是同时成立的前提，不把只满足PD或多卡当充分条件；与balance scheduling、profiling_chunk互斥，recompute是独立同级配置。暂停保留原rank已分配KV，不是迁移、offload、抢占重算或自动释放显存；外部负载路由与本地Out/In/Freeze分别验收。

默认start_step=250，end_step=-1表示无终点；非-1的end_step是排他的已完成快照上限，必须大于start。短测试没到250可能没有计划，不能据日志少判功能坏；诊断才将start_step=0和static打开。快照产生计划由下一步消费，新wave首步无前一步计划，因此计划日志不等于同一步的实际执行或已产生收益。

默认dynamic：新加入请求块数严格大于long_req_block_threshold=700才激活；等于700不满足文档触发条件，也不从已有请求变长推导等同新请求事件。连续dynamic_max_step=256个活动步没有另一新长请求后停用，仍受start/end限制。bubble_threshold默认5.0，以max减average的绝对块差计；低于1才按(max-average)/max算比例，1表示1块而非100%。这些单位依赖实际block size，不能把700默认当700 token。

默认enable_diagnostics=false，rank0详细快照和Out/In/Freeze仅用于短诊断；性能对照前关闭。记录每rank进入采集的步序、remote KV就绪等待、实际暂停/恢复、完成率和服务尾延迟，固定模型/流量/拓扑再测dynamic。均匀负载、DP1、多节点Decode DP维持关闭；投机/async组合依准确版本另验，不从启动或固定启发式推导全模型收益。本批未执行scheduler或NPU服务。


## 当前 planner 的完整程序结构与代价模型边界

本节按固定 ceac1a2 两个文件的整文件AST程序投影核对全部函数体：core/dyntra_lb_scheduler.py 1201原始行、patch_dyntra_lb_core.py 521原始行。投影保留语句/分支/参数/调用，去掉注释和docstring；不冒称逐字全文阅读，也未执行上游或分布式调度。具体注册导入仍需配对平台接线。

负载block数从 cache_config.block_size 算ceil(len(all_token_ids)/B)，先要求B为正int；它不是 scheduler.block_size 或所有hybrid组实际分配块之和。候选表每rank最多2×max_num_seqs个int32槽，running先占、waiting用余量，另带split和新长请求flag；被截断的waiting未进入本次规划，不可把快照当全部排队请求。

planner先按max_num_seqs把waiting补到running，再循环优先给最轻rank换入更大请求、给最重rank换入更小请求，目标是更接近动态平均；只在原rank的running/waiting之间调换。相同距离偏向移出newly-added请求。若无法交换，可按固定模型 latency=20000+19.2×max_blocks 估计是否drop一个running提高总请求数/latency，最多1000轮；常量不是本次硬件测量或模型无关cost。最后抵消同rank成对同块数Out/In，并以没有In标freeze；块数相同的请求不是具名跨rank迁移。

## KV预取、准入与暂停的不同状态

prepare先刷新blocked waiting，再做有界remote KV prefetch：上限2×max_running-len(running)，仅WAITING/PREEMPTED且computed=0候选；远端ext=None、达到prefetch上限或分配失败的请求本次不能准入。异步命中先按0新增token分配/登记外部KV，标WAITING_FOR_REMOTE_KVS并进入inflight，不能在数据未ready时按“有block数”直接运行。

modifications消费时优先暂停标newly-added的同块数running，再匹配其他请求；pause将状态标PREEMPTED、放kv_holding_waiting并保留KV，不调用普通释放/重算。lb_paused集合区分同一个枚举状态下的两种来源。等待队列优先KV-holding，受pending output、LoRA槽、blocked状态和admit集合共同限制；freeze不意味着所有running停跑。

调度器还保留token/model长度/encoder预算、Mamba block-aligned split、lookahead和真实内存抢占。普通OOM preempt会清lb_paused标记，并根据底层版本传drop_stale_output；异步仍有可交付旧输出时暂停请求不能立即重复准入。不能把Out计划等同于释放显存或消费端已经收到最后结果。

## 本地partial命中与外部KV不能相加重复计算

支持connector partial-tail API时，先按block边界询问外部命中。若外部覆盖长度大于本地partial tail，截断本地尾块后取外部；否则保留local tail、外部按0且关闭async。hybrid per-group本地hit分歧而没有外部补充时回原统一lookup。没有该新API的版本走明确fallback，不由hasattr推完整语义兼容。

异步load分配时暂不加lookahead，可按connector声明跳过已加载group的zeroing，并保存inflight reserved blocks；scheduler完成后才构建KV/EC metadata。MRv2把resumed并入new并提供完整token IDs，MRv1仍维护prev-step集合；可选SchedulerOutput字段按dataclass字段探测，不能只按旧签名拼参数。KV block-state只用于构造connector metadata，随后清空，不应让消费者把临时对象当跨步稳定所有权。

## dynamic激活、闲置与验证

dynamic idle期用DP all_reduce(MAX)同步pending长请求及其最大块数，激活后all_gather候选；本步新长请求或刚激活重置计数，否则累计到dynamic_max_step停用。start/end仍独立控制是否产计划。全局无未完成请求时清计划、freeze和prefetch标志；diagnostics包装保留原_has_global_unfinished_reqs调用，不可替换成纯本地空队列判断。

Agent应同时记录计划快照与下一步真正准入/暂停、remote就绪、pending输出、每组命中、token/LoRA/encoder预算和所有rank集合通信顺序。覆盖同块数多请求、截断候选、partial-tail、全部remote等待、busy/idle混rank、优先级抢占与dynamic K。固定启发式减少估计bubble不证明实际吞吐或尾延迟变好；本次无运行结果。
