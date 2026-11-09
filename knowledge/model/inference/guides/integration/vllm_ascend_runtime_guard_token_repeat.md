---
type: Guide
title: vLLM Ascend token_repeat：窗口重读分数、累计游标与告警锁存
description: 解释 push_token_repeat、repeat_sum和content_tokens_seen的精确口径，核对忽略token、chunk内命中、同波去重、异步CPU队列及热变更后的历史重放，区分重复信号与任务质量。
tags:
- task.debugging
- task.testing
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/token_repeat.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/io.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/action/queue.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/schema.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/detector_catalog.py
  role: constraint
created_at: '2026-10-29T18:52:32Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T18:52:32Z'
---

# vLLM Ascend token_repeat：窗口重读分数、累计游标与告警锁存


## 任务与版本

针对重复token误报、长请求未报、参数调后不再告警或chunk统计看似矛盾的排查。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`；标准MRv2接线，整卡平台未定位，保持draft/空平台。仅蒸馏源码，不将该启发式检测视为模型质量评测或已验证的异常根因。

## 分数不是重复比例

默认enabled=False、window=32、repeat_sum_threshold=64、min_tokens=32、consecutive_hits=1、ignore_token_ids=[]。W为window：

1. 非忽略token t的本次score等于它在**加入前**content窗口中的出现次数；随后加入t，将content裁至最近W个非忽略token并更新freq，content_tokens_seen加1。
2. 忽略token本次score=0且不加入content，也不增加content_tokens_seen；但仍加入scores时间序列。
3. repeat_sum为最近W个输入位置score之和；scores窗口包含忽略位置，而content窗口不包含忽略token，二者不是同一序列。
4. 只有content_tokens_seen>=min_tokens且repeat_sum **严格大于** threshold才算本位置over；over则连续命中数加1，否则清零。达到consecutive_hits后，本chunk的hit锁存为True，但还会把其余token全部推入状态。

例如W=3、无忽略项、连续同一token的前四个score为0、1、2、3，第四个位置repeat_sum=6；长期稳态score可为W、repeat_sum可为W²。这不是0到1的比例，不能把64当成64%或套repetition_penalty的语义。上述是手算源码规则，不是本次模型观测。

忽略token并不保证该位置不触发：若此前repeat_sum仍在阈值之上，零score也可继续满足over。min_tokens只数非忽略内容token，不等于总输出长度。需要按实际tokenizer确定忽略ID，不能把另一个模型的特殊token表直接复用。

## chunk、详情和首个命中可能不同步

只要chunk内某位置达到连续命中条件就返回Incident，之后仍处理整个chunk。最终detail里的repeat_sum、last_score、consecutive_hits是chunk末状态；它们可能已回落甚至连续数为0，不能据此否定chunk中途确实命中过。recent_token_ids仅当前增量chunk末最多32个ID，不是完整content窗口或请求全文。

Incident用ILL_TYPE_REPEAT=3；这是检测类型标签，不能证明自然语言语义无效。代码、诗句、格式化输出或业务要求的重复，需要另按任务约束判断，不通过修改质量基准来迁就告警。

## 累计流、游标和一次告警锁存

标准manager只在after-sample把已验证输出写入RequestIoSnapshotManager/RequestGuardStore；after-spec不再重复追加。check_all(sampled_token_ids=None)通过cumulative_output_since和每请求_consumed_len只取新tail。独立调用时若传入sampled rows，会先追加，再走同一游标路径。

Store在同一wave去重相邻相同chunk；下一wave清frontier，合法重复输出才能继续累计。token_repeat还必须用累计游标，不能把被冻结chunk再次评分来绕过Store去重。输入buffer变短时会重建该请求窗口、从现有累计流重新折叠；请求ID复用/旧异步输出仍需按生命周期核验。

一旦本类型告警，req_id进入_alerted集合，后续不再评分；skip/alerted分支仍前移_consumed_len。仅提高report.max_per_req或调整分数阈值，不会自动解除这个检测器私有锁存。clear_finished会删除窗口、游标和锁存；窗口参数变化且已有状态时也会清空它们，下一检查可从Store现有完整累计输出重放，不是只从变更后的新token开始。

只改ignore、min_tokens、阈值或consecutive_hits不清既有窗口/锁存，旧分数可能反映旧规则；启停开关也没有像logits_finite那样清空所有历史。ignore列表校验失败会保留旧ignore，但前面已更新的其他参数未必回滚。正式热配置是否先被总schema拒绝，仍看RuntimeConfig路径；不能把底层setter当成一个原子配置事务。

## 异步检测与覆盖边界

manager把CPU检测交给ActionQueue重任务，队列满或停止时丢弃且不在推理线程内联执行。后续任务可能折叠累计tail，但丢任务、请求先回收、关检测或锁存等情况不能保证逐波补检。工作线程读取执行时的Store，不是冻结在入队时的token快照；arm_wave却来自入队时采样stamp，积压时不能把两者当成严格同时证据。

默认report.max_per_req=1的成功报告还可使请求对**所有**检测器stop-detect。区分检测器_alerted、Store停检、队列丢弃与报告去重，否则“未再报”容易被误解为模型已恢复。共享IO、回收与队列详见[请求生命周期](vllm_ascend_runtime_guard_request_lifecycle.md)。

验收时保留W、阈值、有效token流、忽略ID、chunk边界、游标、wave与report状态，再用任务精度验证实际业务。没有这些条件，不把repeat_sum或单条JSON作为模型适配完成的证明；本次没有运行NPU、检测注入或性能A/B。
