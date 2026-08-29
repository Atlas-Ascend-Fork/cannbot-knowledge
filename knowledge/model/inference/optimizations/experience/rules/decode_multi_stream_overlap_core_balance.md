---
type: Optimization
title: decode 多流并行 overlap：模块级双流控核平衡 + 前处理子链切流
description: decode 多流并行 overlap：模块级双流控核平衡 + 前处理子链切流。decode 时延受限于一条很长的串行算子段（attention/dense 与 MoE 顺序执行；或 Prolog 前处理链堆在主流上），想用多流让互不依赖的部分 overlap 掉时延（multi-stream）。 两种可迁移的切法，按 overlap 粒度选：模块级双流（两个完整模块并行，需控核平衡）与前处理子链切流（把一个算子链拆到多流，需设计同步点）。
tags:
- task.optimization
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/351
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# decode 多流并行 overlap：模块级双流控核平衡 + 前处理子链切流

## 适用场景
- decode 时延受限于一条很长的串行算子段（attention/dense 与 MoE 顺序执行；或 Prolog 前处理链堆在主流上），想用多流让互不依赖的部分 overlap 掉时延（[multi-stream](../../../concepts/techniques/multi_stream.md)）。
- 两种可迁移的切法，按 overlap 粒度选：**模块级双流**（两个完整模块并行，需控核平衡）与**前处理子链切流**（把一个算子链拆到多流，需设计同步点）。

## 切法一：模块级双流 + 控核平衡（attn/dense ‖ MoE）
- 场景：一条流跑 attn/dense、另一条流跑 [MoE](../../../concepts/techniques/moe_multi_stream.md)（router/dispatch/gmm/combine）。
- **控核平衡是关键**：多流下单流独占全部 AI core 会压低另一流的算子并行度 → 用 `limit_core_num` 给主流/副流各分一段 core，使两流计算时间对齐、消除拖尾。判断依据是「让并发两流的计算时间对齐」，不是照搬固定常量。
- 具体分核比例需按模型/负载重新平衡。参考数据点（Atlas A3 LongCat-Flash，仅作起点）：`enable_multi_stream=1` → 主流(dense/attn) c16v32、副流(router/dispatch/gmm/combine) c8v16；`=2` → 双流均 c12v24；stage1 不控核、默认占满全部 AI/vector core。

## 切法二：前处理子链切流（Indexer Prolog 内部拆流）
- 场景：Attention 前处理 / Prolog 类算子链（[Indexer Prolog](../../../concepts/kernels/indexer_prolog.md)：线性投影、RoPE、量化、权重路径准备）全堆主流会形成很长串行段，后续 attention 即使快也要等前处理全跑完。与模块级双流不同，这里**不并行完整模块、而是拆分前处理子链**。
- 做法：把彼此有局部并行窗口的子链分到不同 tagged stream 与主流并行——Q 路径（`q_b` + RoPE）放一条流、`weights_proj` 权重投影放另一条流提前跑；前处理中 Cube 算子与 Vector/quant 路径可形成硬件互补。进入后续 quant/attention 前用 `npu_wait_tensor`（或 tagged event）表达跨流依赖：
  ```python
  enable_multi_streams = self.enable_multi_streams and not is_prefill
  with npu_stream_switch(enable_multi_streams, "22"):
      if enable_multi_streams:
          tng.scope.npu_wait_tensor(qr, query_states[0])
      q_b = self.wq_b(qr, c8_input_dict.get("pertoken_scale", None))
      ...  # q split / npu_rotary_mul
  with npu_stream_switch(enable_multi_streams, "33"):
      if enable_multi_streams:
          tng.scope.npu_wait_tensor(x, q_b)
      weights = self.weights_proj(x.view(-1, self.dim))
  ```
  [torchair](../../../concepts/frameworks/torchair.md) 图模式下再配 tagged stream event（`tng.ops.npu_record_tagged_stream` / `npu_tagged_event_record`），流号与事件生命周期要统一。

## 共同风险 / 边界
- 两种切法都**仅 decode 启用**（`... and not is_prefill`）。
- 切流后同步点设计不清最易出「输入未准备好」；若子链间实际共享更多隐藏依赖，盲目切流会导致图编译失败或精度问题。
- 收益均为定性目标（让串行段出现 overlap），下列证据未给 before→after 数字。

## 参考实现及其约束
- 控核双流参考 LongCat-Flash（Atlas A3，相较原论文四阶段并行把第二段 attention 与 FFN 专家提前执行）；前处理切流参考 DeepSeek-V3.2-Exp 的 Lightning Indexer Prolog（相似 GLM-5），流号 "22"/"33" 与 API 是该参考实现细节。

## 相关经验
- [图模式多流并行的跨流同步：ge_graph 控制边 vs aclgraph tagged-e](../../../guides/experience/interventions/graph_mode_multi_stream_cross_stream_sync_api.md)

## Evidence
- `diff 事实` + `doc 披露`（@0640521a8170）：`modeling_longcat_flash.py` 确认 `npu_stream_switch(True,"1")` + 两处 `limit_core_num`，`enable_multi_stream==1`→(8,16)/(16,32)、`==2`→(12,24)/(12,24) 常量分支，与优化文档「多流并行与控核」一致；性能收益为文档定性披露、不外推。
- `diff 事实`（@d739fecb4232）：`model-infer-multi-stream` skill 的 `indexer-prolog-multi-stream.md` 逐段核对一致，`npu_stream_switch` / `npu_wait_tensor` / `npu_record_tagged_stream` 为切流机制事实；「代表实现 DeepSeek-V3.2-Exp / 相似 GLM-5」为 skill 示例具名披露、未逐字核模型源文件。
- 溯源下探：[cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)、[cann-recipes-infer-pr-351-feat-update-agent-skills-with-full-optimization-pipeline-and-role-based](https://gitcode.com/cann/cann-recipes-infer/merge_requests/351)
- 相关：同 decode 阶段用空闲带宽掩盖搬运的权重预取调度见 [decode-weight-prefetch-ordering](decode_weight_prefetch_ordering.md)。

<!-- cannbot:related:start -->
## 相关

- [NPU 多流优化(Multi-Stream)](../../../concepts/techniques/multi_stream.md)（`related`）：要使能多 Stream 并行，需要计算图中存在满足并行条件的结构：当多个算子的输入都依赖于同一前驱算子的输出、彼此之间没有数据依赖时，这些算子在拓扑上即可并发执行。如下图，前置算子 A 的输出同时被 B 与 C 两条分支消费；B、C 之间无数据依赖，可分别承载于两条 Stream 并行，最终在汇合算子 D 合并。；**控核平衡是关键**：多流下单流独占全部 AI core 会压低另一流的算子并行度 → 用 `limit_core_num` 给主流/副流各分一段 core，使两流计算时间对齐、消除拖尾。判断依据是「让并发两流的计算时间对齐」，不是照搬固定常量。。通用卡确定分支具备并发拓扑，优化卡补上实际并发时避免单流独占核心并校准拖尾的资源约束。
- [decode 访存 bound 阶段的权重预取调度：按搬运 bound 大小排布相邻算子的预取顺序](decode_weight_prefetch_ordering.md)（`related`）：**预取顺序按搬运 bound 大小排布，不是无差别每个都预取**；两种可迁移的切法，按 overlap 粒度选：**模块级双流**（两个完整模块并行，需控核平衡）与**前处理子链切流**（把一个算子链拆到多流，需设计同步点）。；预取排序利用带宽空档，多流切分利用计算流水并行；两卡共同服务 decode 串行段压缩，但分别要求缓存容量排序与跨流依赖设计。
- [图模式多流并行的跨流同步：ge_graph 控制边 vs aclgraph tagged-event 及 API 选型](../../../guides/experience/interventions/graph_mode_multi_stream_cross_stream_sync_api.md)（`related`）：本页只解决"跨流数据依赖在不同图后端下怎么正确表达、别把 API 混写"。；进入后续 quant/attention 前用 `npu_wait_tensor`（或 tagged event）表达跨流依赖：；前者规定后端相关同步合同，后者给出 decode 子链切流后真正需要落等待点的位置，能把 API 规则落到 overlap 实现。
- [图模式多流跨流同步的失败签名：漏配同步/守卫不一致/重复创建 event/流未转发](../../../runbooks/runtime/graph_mode_multi_stream_sync_failures.md)（`related`）：切流后同步点设计不清最易出「输入未准备好」；若子链间实际共享更多隐藏依赖，盲目切流会导致图编译失败或精度问题。；侧流产出的张量在回主流被下游消费前**缺跨流等待**。；优化规则给出切流后输入依赖未闭合的风险，排障卡把同一风险落到生产者回主流前缺 wait 的可观测根因，并给出按跨流边补 record/wait 的检查方向。
- [多流并行后还要分核：limit_core_num 给两条重路径流配不同 Cube/Vector 核数、让时长趋近](../cases/moe_multi_stream_limit_core_num.md)（`same_topic`）：**控核平衡是关键**：多流下单流独占全部 AI core 会压低另一流的算子并行度 → 用 `limit_core_num` 给主流/副流各分一段 core，使两流计算时间对齐、消除拖尾。；`aic_num*/aiv_num*` 不是通用值——控核参数要结合 profile 调整，硬搬别的模型的核数配比大概率不最优。；两端围绕同一 decode 模块双流控核决策，规则定义以两流时长对齐为目标，案例补齐 aic/aiv 两组参数必须由 profile 迭代而不能照搬常量。
<!-- cannbot:related:end -->
