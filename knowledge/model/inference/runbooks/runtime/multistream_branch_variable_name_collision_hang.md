---
type: Runbook
title: 多流 + TP 下 MoE 无报错卡死：排查并发分支复用同名 Python 变量（路由 vs 共享专家）
description: 多流 + TP 下 MoE 无报错卡死：排查并发分支复用同名 Python 变量（路由 vs 共享专家）。在多流（MoE 多流 / multi-stream）叠加 TP 的 MoE 推理下（观测于 16 TP），前向无报错地卡住（stuck / hang），没有任何异常栈，就是不往下走。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/172
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:43:19Z'
platforms:
- agnostic
---

# 多流 + TP 下 MoE 无报错卡死：排查并发分支复用同名 Python 变量（路由 vs 共享专家）

## 信号

在**多流**（[MoE 多流](../../concepts/techniques/moe_multi_stream.md) / [multi-stream](../../concepts/techniques/multi_stream.md)）叠加 [TP](../../concepts/parallelism/tensor_parallel.md) 的 MoE 推理下（观测于 16 TP），前向**无报错地卡住**（stuck / hang），没有任何异常栈，就是不往下走。

## 触发条件

MoE 层同时跑**路由专家分支**与**共享专家分支**、且两条分支被切到并发的不同流上执行；量化路径为 A8W8 / [W8A8](../../concepts/quantization/w8a8c8.md)（`gmm_quant_mode == "A8W8"`）。此时两条分支的中间量若**在 Python 层复用了同一个变量名**，就可能在多流下相互干扰。

## 根因

A8W8 场景下 `npu_moe_init_routing_v2` 与后续 dynamicquant 融合、输出 INT8 数据与对应 per-token scale；路由专家分支把该 scale 命名为 `pertoken_scale`，随后写入 `moe_args["pertoken_scale"]`。而**共享专家分支已有一个同名的 `pertoken_scale` 变量**——两条本应独立、又被排到不同流上的分支复用了同一个 Python 变量名，在多流下产生冲突、卡死。「同名变量为何在多流下导致 hang 而非普通覆盖」的确切流级机制未经独立复现（属推断）；可行动的核心是**症状 → 排查线索 → 修法**这条签名，不依赖对底层机制的完全解释。

## 修法

把两条并发分支复用的同名变量**解耦改名**——本例把路由专家一路的输出从 `pertoken_scale` 改为 `dynamic_scale`，与共享专家的 `pertoken_scale` 分开（`moe_args` 里的赋值源同步改名），卡死即消除：

```python
# A8W8 下 npu_moe_init_routing_v2 与 dynamicquant 融合，输出 INT8 + 对应 per-token scale
- expanded_x, expanded_row_idx, tokens_per_expert, pertoken_scale = torch_npu.npu_moe_init_routing_v2(...)
+ expanded_x, expanded_row_idx, tokens_per_expert, dynamic_scale = torch_npu.npu_moe_init_routing_v2(...)
  ...
  if self.gmm_quant_mode == "A8W8":
-     moe_args.update({"group_list_type": 2, "pertoken_scale": pertoken_scale})
+     moe_args.update({"group_list_type": 2, "pertoken_scale": dynamic_scale})
```

**排查线索**：该固定实现改名后恢复仅为来源自述，不能证明 Python 同名变量天然产生跨流冲突。先核对是否在同一作用域覆盖了仍被另一分支消费的张量、实际消费关系和流依赖，再单独改名并比较相同负载下的时间线与输出；只有复测支持时才采用该实现的修法，不外推到任意同结构 MoE。

## 相关经验
- [aclgraph replay 静默挂死无报错时：用 acl_graph_print 图内打](aclgraph_print_bisect_silent_hang.md)
- [多流注意力主流张量被通信流消费致 NPU 内存不释放：跨流消费前 clone 副本解耦生命周](multistream_cross_stream_tensor_lifetime_clone.md)

- 多流写法本身写错的其它失败签名（漏配跨流同步 / 守卫不一致 / event 重复创建 / 条件创建资源未转发）见 [graph-mode-multi-stream-sync-failures](graph_mode_multi_stream_sync_failures.md)——本页是并列的又一类（并发分支变量命名冲突）。
- 路由 / 共享专家双流重叠的正向干预配方（副流掩盖、同步协议）见 [moe-shared-expert-decode-dual-stream](../../optimizations/rules/moe_shared_expert_decode_dual_stream.md)。

## Evidence

- `diff 事实`（@1a186a32b40d，共 2 行）：`npu_moe_init_routing_v2` 第 4 输出 `pertoken_scale`→`dynamic_scale` 及 `moe_args["pertoken_scale"]` 赋值源同步改名，已对上。症状「多流 + TP + A8W8 MoE 无报错卡死」与根因「路由 / 共享专家 `pertoken_scale` 变量复用」来自作者自述，并有两位维护者批准合并；共享专家侧同名变量的冲突现场未落在 2 行 diff 上下文窗口内，「同名为何在多流下 hang 而非覆盖」的流级机制为推断、未并入事实面。
- 溯源下探：[cann-recipes-infer-pr-172-fix-tp-stuck-bug-fix](https://gitcode.com/cann/cann-recipes-infer/merge_requests/172)