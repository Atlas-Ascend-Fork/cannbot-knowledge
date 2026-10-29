---
type: Runbook
title: 图模式多流跨流同步的失败签名：漏配同步/守卫不一致/重复创建 event/流未转发
description: 图模式多流跨流同步的失败签名：漏配同步/守卫不一致/重复创建 event/流未转发。在图模式多流路径上改动后，出现"多流开关一开结果就不稳 / 图模式 + MTP 执行失败 / 重复创建 event"这类症状时对号入座。正确的跨流同步 API 与写法在 graph-mode-multi-stream-cross-stream-sync-api；本页是那套写法写错时的四种失败签名。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.speculative_decoding
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/269
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/59
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/236
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/497
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-21T01:48:04Z'
platforms:
- agnostic
---

# 图模式多流跨流同步的失败签名：漏配同步/守卫不一致/重复创建 event/流未转发

## 适用场景

在图模式多流路径上改动后，出现"多流开关一开结果就不稳 / 图模式 + MTP 执行失败 / 重复创建 event"这类症状时对号入座。正确的跨流同步 API 与写法在 [graph-mode-multi-stream-cross-stream-sync-api](../../optimizations/rules/graph_mode_multi_stream_cross_stream_sync_api.md)；本页是那套写法**写错时的四种失败签名**。

## 签名 1：aclgraph 下漏配跨流 tagged-event → 静默数据竞争

- **信号**：aclgraph + multistream decode 下结果错误/不确定（无必然报错）。别人遇到"同一路径多流开关一开结果就不稳"可对号入座。触发全条件：多机 + aclgraph + multistream + statickernel。
- **根因**：侧流产出的张量在回主流被下游消费前**缺跨流等待**。典型漏法——原实现只建了覆盖部分边的 tagged event，**跨流边一旦增加、事件对数没同步跟上就静默漏配**（如 indexer 只覆盖"主流→流22""流22→流33"两条边，漏了两条侧流→主流回收边）。
- **修法**：aclgraph 下**每条**跨流生产者→消费者边都补一对 `npu_tagged_event_record`/`npu_tagged_event_wait`（record 紧跟生产、wait 紧接消费前），检查每条跨流依赖是否被有效同步覆盖，以 `enable_multi_streams and enable_aclgraph` 守卫。该 PR 的 GE 路径没有复现同一问题；这不是 GE 不会发生跨流错误的保证——不能以"GE 图跑通/未复现"当作 aclgraph 同步已完备的证据，两后端各自验证。

## 签名 2：`npu_wait_tensor` 守卫比 `npu_stream_switch` 闸门宽 → 单流路径插无效控制边

- **不要做**：在 `npu_stream_switch(cond, ...)` 块内，用比 `cond` **宽**的条件守卫内部 `npu_wait_tensor`。
- **为何**：多流关闭时不切侧流，跨流 wait 失去对象。典型：stream-switch 闸门是 `enable_multi_streams = self.enable_multi_streams and not is_prefill`（默认 `self.enable_multi_streams=False`），而旧 wait-tensor 守卫用更宽的 `not is_prefill`——默认多流关 + decode 时不切侧流却照发 `npu_wait_tensor`，在单流 pass-through 上插入无意义/不一致的图依赖。
- **修法**：内部依赖守卫**复用外层 stream-switch 的同一开关变量**（`if not is_prefill:` → `if enable_multi_streams:`）。

## 签名 3：MTP 触发 tagged-event 重复创建 → 提升为模块级全局

- **信号**：`enable_multi_streams` + `enable_aclgraph` + MTP 启用时，多流同步用的 tagged event 被**重复创建**。
- **根因**：tagged event 原创建在**实例级**（`Indexer.__init__` / `DeepseekV3MoE.__init__` 按 `layer_idx` tag），MTP 启用会额外构建第二张 decode 图使层重新实例化 → 实例级 event 再次创建（"MTP→第二张图→重复"因果为推断）。
- **修法**：把 tagged event **提升为模块级全局变量**，import 时只创建一次、每类 2 个、跨所有层共享；所有 record/wait 从 `self.npu_events[i]` 改指 `indexer_npu_events[i]` / `moe_npu_events[i]`。权衡：全局创建变**无条件**（非多流/非 aclgraph 也在 import 时建这 2+2 个 handle），属可接受的常驻小开销。

## 签名 4：MTP 层委派漏转发 `shared_expert_stream` → 对 None 流 record_stream 崩

- **信号**：`npugraph_ex`（acl_graph）+ MTP + 带共享专家多流 overlap 时执行失败。
- **根因**：`shared_expert_stream`（`torch.npu.Stream()`）**条件创建**——仅 `enable_multi_streams and enable_npugraph_ex` 时该属性存在。基类 `forward` 遍历 decoder layer 时已防御式转发 `shared_expert_stream=getattr(self, 'shared_expert_stream', None)`，但 MTP 层包装 `DeepseekV3ModelMTPLayer.forward` 委派到内层时**漏传**，内层取默认 `None`；多流 overlap 开启（`switch_flag=True`）而流为 `None` 时 `record_stream(True, x, None)` / `with npu_stream_switch(True, None)` 在 None 流上执行而崩。
- **修法**：在委派调用补上与基类一致的转发（新增 1 行）：`shared_expert_stream=getattr(self, 'shared_expert_stream', None)`。**用 `getattr(..., None)` 而非 `self.shared_expert_stream`**——该属性条件创建，其它 exe_mode/单流配置下缺失，直接访问会 `AttributeError`。**可迁移原则**：任何委派到内层 decoder layer 的子类/包装层（如 MTP 层），若内层依赖某**条件创建**的每对象资源（多流、event 等），都必须防御式（`getattr(..., None)`）转发下去。

## 参考实现及其约束

参考实现：DeepSeek-V3.2-Exp 的 `Indexer` / `DeepseekV3MoE` 多流段、DeepSeek-R1/V3 的 `DeepseekV3ModelMTPLayer.forward`。流标签、`enable_aclgraph`/`enable_npugraph_ex` 开关名是本仓落点；四条失败签名（漏配同步、守卫不一致、event 重复创建、条件创建资源未转发）对任何在图模式手写多流同步的路径可迁移。相关 MTP 图模式坑见 [mtp-speculative-decode-graph-mode-prereqs](mtp_speculative_decode_graph_mode_prereqs.md)。

## 相关经验
- [aclgraph replay 静默挂死无报错时：用 acl_graph_print 图内打](aclgraph_print_bisect_silent_hang.md)
- [aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL00](aclgraph_sq_cq_alloc_fail_capture_sizes_budget.md)

- 另见 [多流 + TP 下 MoE 无报错卡死：排查并发分支复用同名 Python 变量（路由 vs 共享专家）](multistream_branch_variable_name_collision_hang.md)。


## Evidence

- diff 事实（@7d1f25d29aff）：indexer 补 q、weights 两对 tagged-event（事件对数=跨流边数），守卫 `enable_multi_streams and enable_aclgraph`；具体报错/精度 PR 未给，症状类别为据 diff 反推。溯源下探 [cann-recipes-infer-pr-269-fix-bugfix-ds3-2-aclgraph-multistream](https://gitcode.com/cann/cann-recipes-infer/merge_requests/269)
- diff 事实（@ef0f82d05d89）：两处 `if not is_prefill:` → `if enable_multi_streams:`，守卫与 stream-switch 闸门取同一开关。溯源下探 [cann-recipes-infer-pr-59-fix-fix-minibatch-1-bug-and-remove-redundent-code](https://gitcode.com/cann/cann-recipes-infer/merge_requests/59)
- diff 事实：实例级 `self.npu_events` 删除 + 模块级 `*_npu_events` 全局创建；"MTP→第二张图→重复"为作者描述+推断、已标注。溯源下探 [cann-recipes-infer-pr-236-fix-duplicate-creation-of-multi-stream-events-when-mtp-enable-skip-guard](https://gitcode.com/cann/cann-recipes-infer/merge_requests/236)
- diff + 代码事实（@2c45117）：MTP 层委派新增 `shared_expert_stream=getattr(self,'shared_expert_stream',None)`，该流条件创建故须 getattr；精确 NPU 崩溃点为据代码路径推断、已标注。溯源下探 [cann-recipes-infer-pr-497-fix-update-modeling-deepseek-py](https://gitcode.com/cann/cann-recipes-infer/merge_requests/497)

## 定位探针与修复验收

先确认执行后端、实际多流开关及是否经过 MTP 包装，画出生产者、消费流和同步边。检查每个 wait 的守卫、事件创建次数及流对象是否传递；挂死时可沿关联图内打点 Runbook 定位。一次只修一个签名，覆盖单流、多流、MTP 和重复 replay，对比输出并检查资源增长；失败时回到单流，保留最小复现。
