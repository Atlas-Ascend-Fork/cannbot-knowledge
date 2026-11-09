---
type: Runbook
title: vLLM Ascend logits_finite 告警归因：异步gate、NaN/Inf分类与请求行映射
description: 按 LogitsFiniteDetector 的预采样gate、延迟队列、finite_kind和_row_to_req解释告警，核对grammar修改、索引缺失的行号回退和丢弃路径，避免把未告警或ill_type=4直接解释成数值已通过或原始NaN。 以logits_indices和query_start_loc定位坏logits行及真实请求，保留缺索引的回退边界。
tags:
- task.debugging
- task.testing
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/logits_finite.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/base.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/detector/manager.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/hooks.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/processor.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_guard/rank_gate.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/observability/runtime_config/_defaults.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/runtime_guard.md
  role: supporting
created_at: '2026-10-29T18:52:32Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T18:52:32Z'
aliases:
- Runtime Guard logits_indices 请求行归因
---

# vLLM Ascend logits_finite 告警归因：异步gate、NaN/Inf分类与请求行映射


## 信号、范围与缺口

出现Runtime Guard的logits_finite告警、finite_kind与预期不符、模型已NaN却无报告，或无法确认告警属于哪个请求。依据Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的检测器、manager、hooks及有关配置。标准MRv2接线，不承诺MRv1、独立310P或全部模型可直接复用；没有整项硬件集合依据，保持draft/空平台。

这是源级判据与归因排查，没有运行NPU或注入故障。KV dump动作、分布式due bus、外部allocator和完整报告持久化链仍需分别核验；检测Incident不是根因证明。

## 先确认检测窗口确实被执行

默认enabled=False、item_sync=False。ConfigBackedDetector的_precheck刷新运行配置；整个batch请求均已在skip集合时可直接返回。None、非Tensor、空Tensor、scan失败、gate等待失败都可能不产生Incident，部分失败仅warning。

hooks仅在检测使能且ActionExecutor gate允许时临时包装model.compute_logits，在上下文的**第一次**调用之后执行检查，并于finally恢复原绑定；它不是扫描模型每次中间logits。自定义模型多次compute_logits时须确认第一次就是目标采样矩阵，不能只看装饰器存在。

设计输入是按请求/采样行组织、最后一维为词表的logits。检测器没有为所有任意维度建立完整形状校验；新框架应核对实际shape、padding和batch映射，不能将非标准布局的空告警视为正常。

## 预采样gate与延迟分类是两份证据

源码先算 `row_finite = torch.isfinite(logits).all(dim=-1)`，再对所有行求all。默认把标量gate非阻塞拷到CPU，在after-sample/get_output的check_deferred里等待；需要时也拷贝logits_indices。gate的row_finite已计算，而logits本体以引用保留，grammar或其他代码之后可能原地写入-inf。

因此预采样发现非有限值，并不保证稍后finite_kind读取的还是原始异常值。item_sync=True在before-sample直接.item()并当场分类；它改善该时点的证据一致性，但增加同步，不能作为无开销默认修法。异步gate D2H失败时会尝试同步路径；query_start_loc在某些fallback也调用.cpu()。仅凭“async”名字不能断言热路径完全没有等待。

类别判定按nan→pos_inf→neg_inf→non_finite顺序查询，同一行多种非有限值只给优先类别，不是完整元素清单。所有此类Incident的ill_type都用4（ILL_TYPE_NAN），因为所对齐ILL表没有独立Inf码；**ill_type=4不证明原始logits一定含NaN**。若延迟时原值已变化，finite_kind=non_finite也不推翻已保存的坏行gate。

## 请求行映射：回退规则必须保留

若坏行数所在的logits总行数等于请求数，使用1:1行号，不物化indices。否则尝试logits_indices，配合query_start_loc前缀，将flat token位置落入 `[qsl[r],qsl[r+1])` 来解析请求。qsl优先取batch.query_start_loc_np，再取runner/batch的query_start_loc；Tensor路径可能D2H。

实际 `_row_to_req` 不只有严格前缀映射：缺少/无法物化indices时，对row<num_reqs仍可回退请求行号；indices存在但qsl缺失时也可能走末尾行号回退。只有最终req_id为空的行才warning并跳过。文档的“不猜请求”应理解为不制造null/虚构ID，不能据此声称每个返回ID都已通过flat-token前缀校验。

新适配必须保留行布局与证据：nrows、req_ids快照、logits_indices、qsl、batch重排、投机采样宽度和padding。索引不足、qsl异常或多采样行对应同一请求时，先核对映射，不能直接按Incident.req_idx修改模型。qsl的np.asarray不保证深拷贝，若本来就是可复用int64数组，其待处理引用是否被后续波次改写仍需目标调用链验证，这是静态风险而非已观察故障。

同一batch内按req_id去重，只留该请求首个坏行的详情；并合发起时和消费时的skip集合，已经stop-detect的请求可不再出Incident。未映射行warning仅展示前16个行号，但另有总数，不能据短列表推断只漏了16行。

## 无报告时逐层排查

check_all及同步分支都返回空列表，命中先进入_deferred；默认还先经_pending_gates。两个队列各以内部上限256约束，超出丢最旧batch并warning_once。关闭检测器会清空pending与deferred；不是稍后重新开启就自动追回这些告警。

manager在after-sample先排空logits告警，再安排CPU token_repeat；标准V2的after-sample还需等真实AsyncOutput.get_output完成D2H及num_sampled裁剪。没有取回输出、请求先被停止检测、队列溢出、无法归因、报告去重/写入失败都可能导致有异常而无最终JSON。分开检查gate、Incident、排队、报告和dump，不用“无文件”证明精度正确。

对齐原始logits/词表布局、实际grammar时点、请求/波次/rank与错误日志；必要时小范围对照item_sync，但任务质量仍按精度基准另验。报告或dump可能滞后、结束请求的KV可能已复用，后续取证沿[请求生命周期](../../guides/integration/vllm_ascend_runtime_guard_request_lifecycle.md)核验。本卡未执行实际采集或提出已验证修复。
