---
type: Optimization
title: 多卡 HCCL 通信组/域构建的规则与陷阱（全秩组哨兵 / MC2 专用域 / 并发流独立域）
description: 多卡 HCCL 通信组/域构建的规则与陷阱（全秩组哨兵 / MC2 专用域 / 并发流独立域）。在昇腾 executor（CommManager / init_comm_group）里构建 HCCL 通信组时，有三条容易踩错、症状各异的规则。做多卡通信组配置或 debug"通信对不齐 / TP 输出异常"时先对照。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/391
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/444
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 多卡 HCCL 通信组/域构建的规则与陷阱（全秩组哨兵 / MC2 专用域 / 并发流独立域）

## 适用场景

在昇腾 executor（[CommManager](../../../concepts/frameworks/cann_executor.md) / `init_comm_group`）里构建 HCCL 通信组时，有三条容易踩错、症状各异的规则。做多卡通信组配置或 debug"通信对不齐 / TP 输出异常"时先对照。

## 规则一：全秩组必须返回 default_pg，不能与单秩组合并返回 None

**症状**：[TP](../../../concepts/parallelism/tensor_parallel.md) 铺满全卡（如 qwen3_moe 16TP，TP 组覆盖整个 world）时输出异常。

**根因**：`init_comm_group()` 用 `group_num`（组数）判组拓扑，两种边界拓扑语义相反却外观都在"组边界 = world 边界"：
- `group_num == world_size` → 每组仅 1 rank → **单秩组**（无实际通信，返回 `None` 哨兵合理）；
- `group_num == 1` → 单组含全部 rank → **全秩组**（应复用横跨全 rank 的 `default_pg`）。

把两者用 `use_default_pg = (group_num==world_size) or (group_num==1)` 合并、命中即 `cur_group=None`，会让全秩组误拿 `None`；调用方据此把全秩组当单秩组处理 → TP rank 计算错误 → TP 铺满全卡时输出异常。

**修法**：拆两分支——`group_num==world_size → None`（单秩），`group_num==1 → default_pg`（全秩）；`moe_ep_group` 因 EP 通信需独占，两分支都排除、保持单独建组。

## 规则二：MC2 dispatch/combine 须建专用、不复用的命名通信域

MoE 走 MC2 融合 dispatch/combine（`npu_moe_distribute_dispatch_v2` / `combine_v2`）时，即使与常规 `moe_ep_group` 覆盖**完全相同的 ranks**，也要为它单建 `moe_ep_group_mc2`（`allow_physical_reuse=False`）、并捕获其 HCCL comm name（`return_name=True` → `get_group_name`）传给算子。原因：① MC2 按 `calc_moe_hccl_buffer_size(...)` 算出的（较大）buffer 建域，与常规组默认 buffer 不同，复用会拿到错误 buffer；② 算子需通过 comm name 显式取通信域句柄。`allow_physical_reuse=False` 强制新建独立通信器、绕开签名缓存与 world-group 短路。

沿用常规 `moe_ep_group`、或不给 dispatch 算子传 group_name，会用错通信域/缺名——曾是 longcat-flash AFD 分离特性 dispatch 算子未拿到独立 group_name 的实际 bug。MC2 算子本身的平台/结构兼容边界另见 [mc2-fused-comm-op-compatibility-fallback](../../../runbooks/runtime/mc2_fused_comm_op_compatibility_fallback.md)。

## 规则三：并发多流须为每条流建独立不复用的通信域

prefill micro-batch 多流模式（[prefill-micro-batch](../../../concepts/techniques/prefill_micro_batch.md)）把一个 batch 拆成多条 micro-batch 在**并发多流**上跑，两条流各自发起 attn_tp 的 TP 集合通信、moe_ep 的 EP 集合通信。若两条流共用同一 HCCL 通信域，第二条流会与主流抢同一通信器。手段：为第二条流的 attn_tp / moe_ep 各注册 `*_group_stream1`（`allow_physical_reuse=False`），与主流同名组物理隔离；前向侧按 `has_group("*_stream1")` 择组，存在即用 stream1、否则回退主组。

**可迁移原则**：凡"独立执行流 / MC2 快 EP 路径"要与主路径**并发或用不同 buffer** 做集合通信，就为它建 `allow_physical_reuse=False` 的独立命名 HCCL 域——不要因为 ranks 相同就复用。更深的 HCCL 并发/buffer 硬件语义未展开，规则停在框架强制层面。

## 参考实现

`executor/utils/hccl_utils.py::init_comm_group`（规则一）、`executor/core/config/comm_manager.py::CommGroupConfig` + 各模型 `init_parallel_comm_group`（规则二/三）。证据覆盖 qwen3_moe（16TP）、[DeepSeek-R1](../../../concepts/models/deepseek_r1.md)、longcat-flash / longcat-flash-lite。掩盖 TP/EP 通信的上层手段见 [hide-moe-attention-tp-ep-comm](hide_moe_attention_tp_ep_comm.md)。

## Evidence

- `diff 事实`（@a957702d，规则一）：`init_comm_group` 旧 `use_default_pg = (group_num==world_size) or (group_num==1)` 拆成两分支；症状"qwen3_moe 16TP 输出异常"为作者披露 + maintainer `/lgtm`。溯源下探：[cann-recipes-infer-pr-391-fix-fix-qwen3-moe-16tp](https://gitcode.com/cann/cann-recipes-infer/merge_requests/391)
- `diff 事实`（@fdd26d2c，规则二/三）：`moe_ep_group_mc2` 以 `allow_physical_reuse=False + return_name=True + calc_moe_hccl_buffer_size` 注册、longcat_flash_lite dispatch 侧 `get_group_name` 由 `moe_ep_group` 改 `moe_ep_group_mc2`；`PREFILL_MICRO_BATCH_SP_TP_EP` 分支注册 `attn_tp_group_stream1` / `moe_ep_group_stream1`。溯源下探：[cann-recipes-infer-pr-444-refactor-comm-manager-refactor](https://gitcode.com/cann/cann-recipes-infer/merge_requests/444)
