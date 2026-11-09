---
type: Guide
title: vLLM Ascend Runtime Guard：V2 检测、异步归因与 KV dump 边界
description: 组织重复token、非有限logits与投机接受率的检测取证，区分报告、D2H完成和last-PP×all-TP覆盖；对照 runtime_guard.po
  中文文档差异与实际接线。
tags:
- task.debugging
- topic.model_serving
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/runtime_guard.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/configuration/runtime_config.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/structured_output.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/hooks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/schema.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/detector_catalog.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/runtime_guard.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/dist.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/bus_worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_bus.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor_report.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/dump.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/report.py
  role: implementation
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-10-29T21:54:22Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Runtime Guard：V2 检测、异步归因与 KV dump 边界

## 适用范围与入口

固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的 Runtime Guard 文档明确限制为标准 ModelRunner V2 接线，MRv1 未接入。本卡不据此声明独立 310P 后端或所有模型都具有同样 hook。目标是取得可归因的线上异常证据，不自动修复模型或证明已定位根因。

默认 detector 和 hot reload 都关闭。通过 additional_config 提供启动 overlay、JSON 路径和热加载选项；启动前修改旧 JSON 会被默认值与 overlay 生成的文件覆盖。详细控制与一轮 dump 见[运行时控制 Runbook](../../runbooks/runtime/vllm_ascend_runtime_guard_controls.md)。

## 检测与异步归因

token_repeat 在采样后处理，logits_finite 在采样前做 isfinite gate，spec_acceptance 使用投机统计。logits 默认把 gate 异步拷回，稍后等待；grammar 等可能已改写原 logits，因此 hit-time 的类别不一定对应原始 pre-grammar 值。需要原始归因时可采用 item_sync，但同步开销需测量。

V2 的 AsyncOutput 在 D2H 和 num_sampled 裁剪后提供 host token。不能把 padded sampled_token_ids 直接加入检测历史，也不能为无法映射的 logits 行猜请求 ID。在线 KV/position meta detector 不在该来源版本，取证用 dump_kv 后离线对比。

## 报告与数据不是同一个完成信号

`dump_attempted` 说明 on_trigger 请求了 dump，不证明数据拷回完成。检测/JSON 报告在 last-PP TP0，KV dump 覆盖 last PP 的所有 TP，其他 PP 不在此范围。请求、wave、DP/TP/PP/CP 标识用于拼装同一次证据，不能混合不同波次。

检测 dump 通常在下一 wave 安排并于 wave 尾执行。finish-wave 仍可能 arm，`request_finished_at_dump=true` 表示缓存可能已释放或复用，张量只能作为可疑证据，不能直接用来认定该请求的计算错误。配置广播、dump 列表提交与完成的时序也不同。

## 验证与回退

从 report-only 开始，注入有明确期望的异常，核对请求归因、截断、配额和各 rank 文件，再增开 dump。另跑关闭 Guard、仅热加载及启用 detector/dump 的受控性能对照；“默认低开销”的设计描述不能代替实际测量。

缺少 hook、请求归因不明、产物跨波次混合或缓存已复用时保留缺口，停止根因结论。关闭 detector/dump 并恢复原始 overlay 可回退；不要将在线取证工具当成模型精度已验收。本文未采集真实服务或执行 NPU A/B。

## Structured Output 与检测时点

固定结构化输出指南只声明接口随上游 vLLM，没有给出独立 Ascend parser 或新配置。因此本卡不生成额外 Ascend 专属 guided-decoding 参数。语法约束对 logits 的修改与 Runtime Guard 捕获时点分开核对；检测报告不能单独证明用户 JSON schema 已满足，仍需解析和 schema 验证。


## 平台证据待补

两份完整Runtime Guard/配置指南限定标准MRv2接线和rank范围，但不声明整项检测/dump的平台集合；通用Runner接入不构成硬件支持表。本卡据此撤回原平台枚举，保持draft、空平台；已有机制与操作条件保留为待验证知识。取得针对本功能的明确硬件范围和组合证据后再更新状态，不能把本次修正解读为这些硬件不支持。


## 三个检测器的实际消费口径

重复不是固定比例，按[token_repeat窗口与锁存](vllm_ascend_runtime_guard_token_repeat.md)核对累计游标、忽略ID和chunk末详情；投机按[spec_acceptance双阈值](vllm_ascend_runtime_guard_spec_acceptance.md)核对去bonus、真实draft、窗口就绪和严格双条件，不与逐位置Prometheus指标混用。

非有限值按[logits归因Runbook](../../runbooks/precision/vllm_ascend_runtime_guard_logits_attribution.md)区分gate与延迟kind。实际_row_to_req在索引缺失等情形存在行号fallback，不能把所有Incident.req_id都解释为已严格经flat-token前缀验证；无法归因的剩余行才warning跳过。ill_type=4也不单独证明原始NaN。

## 接线、状态与扩展

请求完成、报告写入和KV仍归原请求是三层证据，详见[请求生命周期](vllm_ascend_runtime_guard_request_lifecycle.md)。标准V2要等inner.get_output完成D2H和裁剪再追加IO；CPU检测、report去重/上限、队列丢弃和8波回收上限都可能影响覆盖，不用“未再报”证明异常已修复。

DetectorSchema/ConfigField与detector_catalog声明默认值、字段和校验；DetectorManager另有构造顺序与各stage的显式调用。只把类加进catalog不会自动把新detector接到所有运行阶段。新增适配需同时核对实例注册/incident_type唯一性、stage gate、有效req映射、异步时点与动作/报告链；这是源码结构推导，不是已经实现的新插件能力。


## 配置同步、dump完成与报告消费

多rank接入按[单槽总线与波次](vllm_ascend_runtime_guard_collective_sync.md)核对writer/source/rank、idle调用、submit/drain和有效配置；last-PP TP的merged总线并非跨DP全局同步。配置本地digest与follower mtime version的判据也不同，不能只看来源日志认定全组生效。

沿[KV dump完整性](../../runbooks/validations/vllm_ascend_runtime_guard_dump_incomplete.md)分别确认arm、同步D2H、heavy queue与.pt保存；dumped日志或manual done不证明全部文件。Reader的group0 block IDs、dim0布局假设与MRv2扁平K/V部件的层名映射须另验，不能仅凭文件名改模型。

消费JSON按[报告产物合同](vllm_ascend_runtime_guard_report_artifacts.md)区分窗口与累计计数、每行截断、降级值、pair限流和实际wave目录。字段存在不是完整性证明；这些都是固定Host实现知识，没有替代实际NPU、精度/性能或下游Agent验证。

## 中文PO对照

runtime_guard.po的43个有效非空条目已与当前英文逐项复核，均无obsolete/fuzzy且msgid可在当前英文找到；本批把它作为补充来源绑定。译文保留“无法归因不猜请求”的文档概述，仍须按实际_row_to_req的fallback限定，不能据中文措辞抹掉源码差异。PO复核不证明生成替换或线上中文HTML已更新；未执行上游生成器。


## 结构化输出的独立验收入口

接入JSON/grammar先按[单backend与grammar生命周期](vllm_ascend_structured_output_backend.md)确认校验、实际库与终态；按[mask行和投机接线](vllm_ascend_grammar_mask_contract.md)区分原始logits与语法禁止项。最终输出沿[schema/流式/错误后恢复验收](../../runbooks/validations/vllm_ascend_structured_output_acceptance.md)执行独立oracle；检测报告不替代该验收，指南“接口相同”也不能代替实际补丁/Runner组合核对。
