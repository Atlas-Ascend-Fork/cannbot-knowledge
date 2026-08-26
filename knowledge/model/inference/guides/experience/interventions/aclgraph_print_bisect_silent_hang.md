---
type: Guide
title: aclgraph replay 静默挂死无报错时：用 acl_graph_print 图内打点二分定位挂点
description: '昇腾 NPU 上开 aclgraph（npu-graph-mode 的 acl_graph / cudagraph_mode: FULL_DECODE_ONLY）后 decode 阶段静默挂死、无 HCCL 报错无 traceback（典型伴 shm_broadcast 60s 超时循环、plog 空只有 TBE subprocess 空 error）时的图内定位干预配方。先排除 eager 路径确认问题在图捕获/replay 侧；因图在 device 上 replay、host 侧 Python 栈与 print 失效，须用图内打印原语 acl_graph_print(<msg>) 作探针随图 replay 输出，再二分挂点：探针成对包夹可疑段（如 event.wait 前后）、多机只 rank0 打印，看哪条不再输出即为挂点上界，把探针不断前移直到第一个仍能输出的位置，挂点夹在最后一个能打印与第一个打不出之间；某 forward 内探针全无输出则挂点在进入该 forward 之前，边界继续上移（参考实现即由 attention 推进到 MoE finalize 跨 DP 组通信不匹配）。关键约束：acl_graph_print 只能在 custom op 内部用（放外面过不了 dynamo trace 而失效），只依赖 CANN/torch_npu 版本、调用无需额外参数，此约束绑定 acl_graph_print+dynamo 参考实现、换 torchair GE 图路径机制不同但探针必须进图的原理不变。纯诊断只定位不改行为、无 rollback 负担、调试完移除即可；GDB 因缺 debug symbol 常徒劳。场景涉及 vLLM-Ascend DP+TP+EP aclgraph decode、MLA、MoE decode。'
tags:
- task.debugging
- topic.attention
- topic.mixture_of_experts
- topic.graph_execution
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/4426
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# aclgraph replay 静默挂死无报错时：用 acl_graph_print 图内打点二分定位挂点

## 适用场景

昇腾 NPU 上开 aclgraph（[npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md) 的 acl_graph / `cudagraph_mode: FULL_DECODE_ONLY` 等）后，decode 阶段**静默挂死**：没有 HCCL 报错、没有 traceback，典型伴随 `shm_broadcast` 60s 超时反复循环（分布式看门狗层面的次生超时，非根因），plog 里也无有效信息（只有 TBE subprocess 的空 error）。普通日志和 Python 层栈都无法定位卡在哪一层。

判断是否落在本页范围：

- **必须先排除 eager 路径**——把 aclgraph 关掉、走 eager 若不挂，则问题在图捕获/replay 侧，本方法适用；eager 也挂则挂点与图无关，另找。
- 若挂点确为通信相关，plog 里本应留有信息、server 本应抛清晰 HCCL 错误。**plog 空 + 无 HCCL 错**恰恰是"这不是常规 HCCL 报错型挂死"的信号，才需要图内打点二分。
- 图捕获后 Python 栈已失效（图在 device 上 replay），断点/print 打在 host 侧 Python 代码里对 replay 挂点无效——必须把探针打进**图内**。

## 技术：图内打印原语 + 二分挂点

**核心思想**：aclgraph 把一段计算固化成 device 上可 replay 的图，挂死发生在 device replay 期间，host 侧无从观测。需要一个**能被捕获进图、随图一起 replay 时输出**的打印原语，作为图内探针；再用二分把挂点夹逼到"最后一个能打印"与"第一个打不出"之间。

- **为何有效**：图内探针随 replay 执行，它是否输出直接反映 replay 是否推进到该点。挂点上界 = 第一个不再输出的探针位置；把探针不断**前移**，直到找到第一个仍能输出的位置，挂点即被夹在相邻两探针之间。
- **能解决什么**：定位常规日志/栈完全失效的图内静默挂死，本案例实证的是跨组通信方法不匹配导致的等待；原理上同理可覆盖跨流同步死锁、算子内部死循环等图内推进被卡住的场景。它**只定位、不改行为**，是纯诊断手段。

## 前置条件

- 图内打印原语（本参考实现为 `acl_graph_print(<msg>)`）**只依赖 CANN / torch_npu 版本**、调用无需额外参数（只传要打印的字符串标签），一般现有版本即可用。
- 若本地框架尚无该方法，可自行补上对应 wrapper——它不引入新的运行期依赖。

## 做什么

1. 在**怀疑区间**内插入图内探针（成对包夹某段可疑操作，如 `event.wait` 前后各打一条），多机场景只让 rank 0 打印以免刷屏：
   ```python
   if forward_context.capturing:
       stream = torch_npu.npu.current_stream()
       event = torch.npu.ExternalEvent()
       if torch.distributed.get_rank() == 0:
           acl_graph_print("Before event wait")
       event.wait(stream)
       if torch.distributed.get_rank() == 0:
           acl_graph_print("After event wait")
       event.reset(stream)
       graph_params.events[num_tokens].append(event)
   ```
2. **二分前移**：跑一次 replay，看哪条探针不再输出。若怀疑点整段都没打印，就把探针不断**往前**移，直到找到第一个真正能输出的位置——挂点就在"最后一个能打印"与"第一个打不出"之间。
3. **区间收敛后越界判断**：若某个 forward（如 attention forward）内探针**一路全无输出**，说明挂点在进入该 forward **之前**，把探测边界继续上移到上游模块（本参考实现即由此从 attention 推进到 MoE finalize 的跨 DP 组通信）。

## 关键约束（参考实现的限制，非技术本身限制）

- **只能在 custom op 内部使用**：`acl_graph_print` 放到 custom op 外会**过不了 dynamo trace** 而失效（`it cannot pass dynamo`）。这是该原语与 dynamo 捕获管线交互的约束——插桩点必须落在会被下沉为 custom op 的代码里。
- 这条约束绑定的是"acl_graph_print + dynamo trace"这一具体参考实现；换用其它图模式后端（如 [torchair](../../../concepts/frameworks/torchair.md) 的 GE 图路径）时打印/探针机制不同，"custom op 内"这一限制不必然照搬，但"探针必须进图、host 侧打点对 replay 无效"的原理不变。

## correctness 验证 / benchmark

- 本方法是诊断手段，不改变模型输出、无功能正确性需回归。
- "验证"即观测探针是否输出：定位成功的判据是探针输出序列在挂点处**恰好断裂**（前有输出、后无输出），据此圈定挂点区间。

## 风险 / rollback

- 只做定位、不改行为，**无 rollback 负担**——调试完把插桩移除即可。
- GDB 是备选，但图模式下通常缺完整 debug symbol、往往徒劳，故优先图内打点。
- 探针本身进图会略改捕获内容，定位结束务必移除，避免污染生产图。

## Outcome（参考实现）

依此法确认 attention `forward` 内打印全无 → 挂点在进入 attention 之前，最终定位到 MoE finalize 的跨 DP 组通信方法不匹配（该失败签名另见同 issue 的 `moe_decode` 静默挂死条目）。场景为 DP+TP+EP 下的 vLLM-Ascend aclgraph decode（[npu-graph-mode](../../../concepts/techniques/npu_graph_mode.md) 的 acl_graph 路径）。

## 相关经验

- 图模式多流跨流同步写错的失败签名（漏配同步 / 守卫不一致 / event 重复创建 / 流未转发）见 [graph-mode-multi-stream-sync-failures](../../../runbooks/runtime/graph_mode_multi_stream_sync_failures.md)——那类挂死同样"静默、无报错"，可与本页的定位手段配合。
- 多流 + 并行下 MoE 无报错卡死的另一类根因（并发分支复用同名变量）见 [multistream-branch-variable-name-collision-hang](../../../runbooks/runtime/multistream_branch_variable_name_collision_hang.md)。

## Evidence

- `acl_graph_print` 的用法、custom-op-内约束（`cannot pass dynamo`）、版本依赖（只依赖 CANN / torch_npu 版本）与二分定位方法论，均来自 issue 讨论中维护者的说明；原语出处为其引述的合入 PR，据此推进到 MoE finalize 定位。层级为维护者确认的用法与约束。
- `acl_graph_print` 内部实现未见 diff（issue 无 diff），本页据实到维护者确认的用法与约束，不外推其实现细节。
- 溯源下探 [vllm-ascend-issue-4426-bug-report-vllm-server-fails-when-using-cudagraph-mode-full-decode-only](https://github.com/vllm-project/vllm-ascend/issues/4426)
