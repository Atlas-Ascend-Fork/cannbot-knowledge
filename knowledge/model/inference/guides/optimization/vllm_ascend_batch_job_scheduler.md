---
type: Guide
title: vLLM Ascend 离线任务调度：Job 分组、EWMA 与 KV 预留
description: 结合中文离线批处理指南，核对request ID任务分组、EWMA与块/token阈值，记录实际调度类、KV预留和最长等待，保留无防饥饿限制。 补充10样本估计冻结、max_jobs零值/历史寿命、下一轮预留、混合类别排序与候选非完整准入的实际实现边界。
tags:
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/batch_job_aware_scheduler.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/batch_job_aware_scheduler.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/core/batch_job_aware_scheduler.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/core/test_batch_job_aware_scheduler.py
  role: evidence
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T02:11:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- BatchJobAwareScheduler
- JobDecodeEstimator
- RunningBlockReserver
- BatchJobAwareRequestQueue
---

# vLLM Ascend 离线任务调度：Job 分组、EWMA 与 KV 预留

## 适用范围

固定指南当前只声明 offline batch 模式。目标是吞吐和设备利用率，未实现 starvation prevention；不能因概述提到“不关心等待的在线场景”就给严格时延服务开启。使用 V1 engine 的调度框架不等于强制选择 Model Runner V1，二者是不同层次。

## 配置与请求归组

在 additional_config.scheduler_config.batch_job_sched_config.enabled 置 true，沿目标版本 run_batch 入口验证。请求 ID 含 `#job_name[名称]#` 才按任务分桶；没有标记全部进入 __default__。只改 custom_id 而实际请求 ID 未保留标记，需要沿入口核对。

策略将 LPT、KV 预留和任务优先级组合：资源充分时偏向长 decode job，资源紧张时偏向短 job，用短任务填补空隙。decode 长度以纯 EWMA 估计，无样本默认128，首观察初始化，后续递推；冷启动预测不是实际 max_tokens。

## 参数与边界

来源默认 max_jobs=20、reserve_margin_blocks=2、reserve_max_blocks=8、low_available_tokens_threshold=4096、short_decode_token_threshold=32。预留参数用块，优先级阈值用 token，不能互换。结合真实输出长度和 block size 调整，不能无限预留造成有效容量下降。

## 验证与回退

在同一批任务比较整体完成时间、有效 tokens/step、抢占、KV 使用、每 job 完成分布及最长等待。检查冷启动与长度突变时的估计误差，缺 job 标记不能算多任务策略已生效。SRF 与本策略互斥。公平性失败、任务长期等待或吞吐下降时关闭 enabled，恢复基线调度。本次为源码和文档核对，未执行批任务。


## 平台证据待补

主指南仅写Ascend NPU与offline/V1 engine前提，未给具体产品集合；不能自行枚举为A2/A3/950。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 中文批处理指南的阈值、输入与饥饿边界

batch_job_aware_scheduler.po的42条译文对应当前英文。概述允许“不关心等待时间的在线场景”是使用动机，启用章节仍明确目前仅支持offline batch；继承chunked prefill/async等功能的概述也不证明任意版本、Runner和其他scheduler组合可用。保持V1 engine、具体run_batch入口与实际scheduler类三项证据，不把吞吐目标当公平性保证。

可用token数大于4096时偏向长decode作业，等于或小于时偏向短作业；这是资源阈值。short_decode_token_threshold=32是另一分类阈值，EWMA无样本128是长度估计，reserve_margin_blocks=2/reserve_max_blocks=8用块；四者不是同一个容量或max_tokens开关。max_jobs=20是跟踪作业数，不是并发请求数，也不保证20个作业公平轮转。降低资源阈值能让长作业更常优先，是需要同负载验证的调参方向，不是无条件吞吐提升。

请求归组按实际request ID中的#job_name[...]#，未标记归__default__仍可进入KV预留/LPT路径；只见custom_id不同不证明分了作业。指南给custom_id和body.request_id双标记样例，要在目标入口确认传递后的真实ID。示例JSONL中的注释行不是JSON对象，说明中的additional_config双冒号也不是可直接使用的JSON；使用其合法嵌套结构并保留解析后的有效配置。没有执行批任务、统计最长等待或获得吞吐结果。


## 固定 Main 调度实现：估计寿命、预算与真实候选顺序

本节全文读取batch_job_aware_scheduler.py685行，另有界读BatchJobSchedConfig1525–1561及专项UT187–215/452–498/661–729。它只闭合Ascend队列/估计/预留合同，Native Scheduler/AsyncScheduler的完整执行循环没有在此重读；未导入上游、构造调度器、运行UT或NPU。旧文档的理想策略与当前实现细节分别保留，不把注释或测试名字当行为真值。

### EWMA 不是无限在线更新

JobNameParser用search查实际request_id中的非空且不含嵌套方括号的job标记，并缓存结果；无标记/空名进__default__。request释放后移除该ID缓存，不等于清掉job估计。JobDecodeEstimator在无统计时预测128，首个观察直接初始化，随后alpha0.1递推、取int返回；每job最多只接受10次观察，此后固定，不继续随工作负载漂移更新。

观察发生在_free_request且status精确为FINISHED_STOPPED时，值取num_output_tokens；长度上限结束、abort或其他终态不会仅因请求离开就自动进入训练样本。估计因而偏向此自然停止样本，不能把所有完成请求的均长当真实内部预测。是否需要更换估计/策略应另做工程变更，本卡不修改上游。

max_jobs同时用于活动bucket与历史job统计，但两者生命周期不同：bucket空后删除，历史_job_stats没有此回收路径。配置允许0，队列把0当不限制bucket；estimator创建统计却直接比较len>=max_jobs，0时第一个新job观察即可触发RuntimeError。这是静态可达风险，未运行复现；不要将max_jobs=0生成成“已支持无限作业”的配置。UT名zero_allows_unlimited实际传max_jobs=51、观察50个job，没有验证0。高基数job名、跨多批复用进程和统计达到上限需实测，不把并发少于20当历史job数不会越界。

### 预留针对下一轮，不是已经锁定的 KV

RunningBlockReserver先模拟本轮token推进，再按推进后位置估计下一轮需要的新块；decode按1+num_lookahead_tokens，prefill按剩余prompt和max_num_scheduled_tokens截断。block边界的remaining取0；还未推进的num_computed不能直接作为下一轮起点。该模拟并不读取最终每请求本轮真实分配，不能当所有KV组、chunk或异步状态的精确容量证明。

原始需求相加后加reserve_margin_blocks，再以reserve_max_blocks截顶；空running仍保留margin。每轮schedule开始invalidate，同轮running数量不变复用、恰增1则只加尾请求，复杂长度变化全算。缓存依赖这一调用与变更协议，不能仅因长度相同推任意替换/修改后的内容也被识别。预留是准入预算扣减，没有在此实际分配或锁住物理块。

admission_budget=max(0,(free_blocks-reserve_blocks)*block_size)，资源4096阈值比较的是扣预留后的此预算。队列bool调用_find_admittable，而len返回排队数；budget为0时可出现len>0但bool=False，应区分有请求、可选候选和真正分配/执行，不能直接报告“队列空”。

### 冷启动、分类与 best-fit 的精确边界

每job bucket前3个加入请求获得cold-start标记，计数不是已完成样本数；bucket删除会重置该计数，历史EWMA仍可存在。冷启动在预算>0后优先选，并不在此要求完整prompt小于预算。prepend也走add，不恢复全局严格FIFO或原位置，不能把LPT队列当普通FCFS。

分类实际为预测长度>short_decode_token_threshold才进long，否则short；等于32属于short，修正类注释中<32/ >=32的边界描述。long/short都存在时，两组内部都按长度降序，再由资源预算决定long-first或short-first；只有一个类别时，高预算降序、低预算升序。因此“资源紧张就所有任务严格最短优先”并非此实现合同。

每job按prompt长度维护bucket：先取不超过搜索预算的最大长度，若一个也没有则返回最小的超预算请求，而不是无候选；同长度队列取头部。最终是否能chunk、准入、分配并执行仍由Native scheduler处理，不用队列选中证明整个prompt一次装入。peek缓存到pop后才清，本卡未闭合任意外部队列变更交错的正确性。

### Agent 调度验收证据

源码声明目标仍为离线吞吐。BatchJobAwareAsyncScheduler以AsyncScheduler、BatchJobAwareScheduler多继承组合，但类存在和MRO说明不证明与所有Runner/connector功能组合通过。保留实际调度类及Native版本，记录job标签、终态样本、前10次估计、历史/活动job数量、raw reserve/capped reserve、真实free blocks、候选与最终scheduled tokens、抢占及最长等待。

所读UT只定义有限job cap、10样本后冻结、预留模拟和若干排序结果，未执行，也没有关闭饥饿或所有交错风险。先用相同任务集比较有效token、整体完成时间与等待分布，再调整margin/cap/阈值；queue bool变假、预留增加或某些短任务更早完成都不单独证明吞吐、公平性或NPU性能改善。
