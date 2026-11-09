---
type: Guide
title: vLLM Ascend spec_acceptance：去bonus的窗口比率与双阈值漂移检测
description: 对照 SpecAcceptanceDetector 的accepted_count、draft_len、acceptance_rate和acceptance_len，核对窗口填满、严格双条件、采样padding与热变更；区别于Prometheus逐位置接受率及性能收益。
tags:
- task.debugging
- task.testing
- topic.speculative_decoding
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/spec_acceptance.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/hooks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/io.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/state.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/rank_gate.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/schema.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/_defaults.py
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

# vLLM Ascend spec_acceptance：去bonus的窗口比率与双阈值漂移检测


## 任务与固定边界

用于解释Runtime Guard的投机接受率偏低/偏高告警，或配置已开却一直无报告。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的SpecAcceptanceDetector及标准MRv2 hooks。尚无整项硬件范围，保持draft/空平台；不把高接受率当成质量好，也不把低接受率直接当成draft模型适配错误。

## 默认参数与入口门禁

默认enabled=False、window=10、low_threshold=0.3、len_low_threshold=1.4、high_threshold=0.96、len_high_threshold=2.8。schema约束window>=1、rate阈值各在[0,1]、长度阈值>=0；声明的字段校验不能替代实际接线和业务校准。

check_all须通过检测开关，runner.speculative_config非None，有请求ID且accepted_token_nums非None。check_one还要求last PP，draft_len>0；manager另按last-PP TP0门禁。短accepted列表/短sampled行会跳过相应请求，不能把无Incident统一解释为正常。

req_state优先用runner.requests[req_id]，否则从input_batch.num_draft_tokens_per_req构造轻量状态。prev_num_draft_len<=0时，退回normalize后的sampled行宽减1。这里normalize不是filter_valid_token_ids，不主动删除-1 padding；应核对上游postprocess_sampled和真实draft长度，不能以一个固定padded宽度证明提出了那么多有效draft token。

## 四个计数口径分开

对请求每个进入窗口的采样步i，设accepted_token_num为Aᵢ、draft_len为Dᵢ：

```text
accepted_draft_i = max(0, A_i - 1)  # 去掉bonus/普通采样位置
acceptance_rate = sum(accepted_draft_i) / sum(D_i)
acceptance_len  = sum(accepted_draft_i) / 当前窗口步数
```

accepted_norm是sampled_norm[:Aᵢ]（Aᵢ>0时），用于窗口证据；accepted_count仍是输入Aᵢ，sampled_count是normalize后行宽。不要把acceptance_len解释成含bonus的平均总输出长度。实现没有把accepted_draft强制裁到draft_len，坏元数据可能产生大于1的比率；先验证计数合同，而不是把它当作新的性能上限。

例如两步D分别为2、4，A分别为2、3，accepted_draft为1、2：窗口rate=3/6=0.5，len=3/2=1.5。rate是按总draft加权的比率，不是逐步rate的简单平均；示例仅是算式说明，未运行模型。

## 告警需要窗口就绪和一对严格条件

只有len(history)>=window才评估，并且满足以下任一组：

```text
(rate < low_threshold  且 length < len_low_threshold)
或
(rate > high_threshold 且 length > len_high_threshold)
```

相等不触发；只越过一项也不触发。窗口单位为检测采样步，不是请求数、输出token数或秒。长度上限/投机策略改变后，原长度阈值可能不再适配；先固定真实draft预算与停止规则，再校准，不能仅改窗口让告警消失。

history保存每步accepted_draft、draft_len和采样/接受ID。热变更window/阈值会复用已有history，并在后续检查按新window裁短；没有token_repeat那种独立的一次告警锁存，也没有按wave去重历史的逻辑。自定义适配器重复调用check_after_spec会推进窗口，不能假定该检测器天然幂等。

## 取证与日志

detail提供窗口总量、各step统计、窗口采样/接受ID、当前行和阈值；它不是整个请求的累计I/O，完整prompt/output由报告阶段另合并。manager在after-spec不向累计IO再追加，以免MTP/Eagle两处hook翻倍。

候选告警可打印INFO，普通步/窗口刚填满主要是DEBUG，短日志受内部2秒节流；on_alert_armed另有日志。没看到INFO不证明hook没执行，反过来有INFO不证明JSON或dump已经写完。Incident的is_ill=True但ILL_TYPE_NONE=0是此类型的编码选择，不是“检测结果没有异常”。

本检测按请求窗口计算，与[benchmark判据](../../runbooks/validations/vllm_ascend_benchmark_verdict_contract.md)中Prometheus前后差分、总draft为分母的**逐位置**接受率不同；更不等于verify/commit开销、平均加速比、TPOT或质量结论。

核对版本、Runner、rank、请求ID、真实draft/accepted/padding、窗口调用次数、report cap与队列，再按[请求生命周期](vllm_ascend_runtime_guard_request_lifecycle.md)追踪输出和报告。最终仍要保留原精度门槛并测量关闭观测的性能。本次未运行投机解码、异常注入或硬件A/B。
