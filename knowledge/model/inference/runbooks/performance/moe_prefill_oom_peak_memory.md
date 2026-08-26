---
type: Runbook
title: MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置
description: MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置。expert-parallel MoE 模型在长序列 prefill 阶段 device OOM（EL0004 Failed to allocate memory / out of memory），常发生在 MoE 的 grouped_matmul 或 dispatch 展开处；同配置换短输入 / 小序列不复现。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/13
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/124
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/427
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/11
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置

## 信号（现象）

[expert-parallel](../../concepts/parallelism/expert_parallel.md) MoE 模型在**长序列 prefill** 阶段 device OOM（`EL0004 Failed to allocate memory` / `out of memory`），常发生在 MoE 的 `grouped_matmul` 或 dispatch 展开处；同配置换短输入 / 小序列不复现。

## 触发条件与根因

峰值内存由两类机理在长序列 prefill 下放大：

- **专家负载不均 → 个别卡的 grouped_matmul 峰值内存爆**。两个常见成因：
  - **padding 引发的负载倾斜**：`input_max_len` 是给长序列数据集设的；实际输入远短于它时会填入大量 padding，导致 MoE 专家负载不均（不是单纯序列长度问题，而是 padding 引发的专家负载倾斜）。
  - **极端路由不均**：长序列请求本身的 Routing 分发存在极端不均，个别卡承接过多 token。
- **dispatch 展开中间量随 token 数线性放大**。MoE 专家 dispatch 把每 token 复制到其 top_k 个专家上，产生 `expanded_x` / `gathered_tokens` 中间张量，规模约 `num_tokens × top_k × hidden`；token 越多峰值越高。用 MC2 融合通信的 dispatch（`npu_moe_distribute_dispatch_v2`）里 `expand_x` 更是**按最大可能输出 shape 静态分配**内存，长序列 prefill 下额外内存占用大、易 OOM。

## 修法（按可用手段选，可叠加）

**（一）均衡专家负载**（针对 padding / 不均成因）：
- 对齐 README 指定的长序列数据集，使实际输入接近 `input_max_len`、避免大量 padding（推荐、已验证生效）。
- 置 `perfect_eplb: True`（EPLB 强制专家均匀负载）——若置 True 后能跑通即确认 OOM 由负载不均导致（确诊 + 缓解）。
- 下调 `input_max_len`（如 65536→32768）减小单卡激活 / KV 显存（规避、非根因修复）。

**（二）沿 seq / token 维分块 dispatch / combine，router 不分块**（针对中间量放大）：
- 引入 `moe_chunk_max_len`：当 `num_tokens > moe_chunk_max_len` 时按 `ceil(num_tokens/moe_chunk_max_len)` 沿 token 维把 `hidden_states / topk_ids / topk_weight` 均分，逐块串行做 expert dispatch/combine，使每块 `expanded_x` / `gathered_tokens` 稳定在 `~ moe_chunk_max_len × top_k × hidden`。
- **router 必须在全量 token 上运行一次、不分块**（top-k 选择要看全量 token 才正确）；分块只作用于 dispatch/combine 段。
- **只在 prefill 分块**（decode token 数少、走原路径不受影响）；`moe_chunk_max_len` 取默认大值（或大于 prefill token 数）即等价不分块，无需改代码，天然可 rollback。代价：各 chunk 串行会对 prefill 性能有相应影响。

**（三）prefill 用 double-routing 而非 dispatch/combine**（EP 场景，针对静态大 shape 分配）：
- 纯 EP（`moe_tp_size==1`）的 prefill 走 `moe_infer_double_routing`（手写 AllToAll 路由），**不用** decode 的 dispatch/combine——因为 double-routing 每张卡只拿到本卡专家要算的 token，峰值内存更低、无内存冗余占用，通信量也更低。
- 机制：init-routing → `all_to_all_single` 按每卡实际 token 数（不是最大 shape）分发 → re-routing → GMM → combine → finalize（每卡 2 次 routing，故名 double-routing）。
- **仅 prefill 用**：decode 反而推荐 dispatch/combine（decode token 少、MC2 融合通信更优）。同一「prefill double-routing / decode dispatch-combine」模式在本仓多个 MoE 建模文件复用。

## 参考实现及其约束

参考 cann-recipes-infer 的 [deepseek-v3.2-exp](../../concepts/models/deepseek_v3_2_exp.md)（padding / double-routing）、LongCat-Flash（`moe_chunk_max_len` 只对 prefill 生效）、Hy3-preview（手动 EP `npu_moe_init_routing_v2 + all_to_all` 链、`_split_tensors` 分块 + router 不分块）。`moe_chunk_max_len` 默认值、示例 config 值（如 `1024`）为参考实现细节。「dispatch 的 expand_tokens 按最大 shape 分配」属维护者确认（算子内部定形、仓内不可见），无独立复测的峰值内存数字。

## 相关经验
- [MoE token dispatcher 把中间张量挂 self. 属性阻止 GC：aclg](moe_token_dispatcher_self_attr_oom_aclgraph.md)
- [profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影](profile_run_peak_memory_underestimate_untraversed_path.md)

- 另见 [配了 enable_profiler 却拿不到 prefill profile：长输入超 moe_chunk_max_len 时被静默门控关闭](../validations/prefill_profiler_gated_off_long_input.md)。


## Evidence

- `维护者确认` + `config 事实`（@2c45117）：padding → MoE 负载不均 → OOM，对齐数据集 / `perfect_eplb` 生效；复现者回帖验证。
- `diff 事实` + `doc 披露`（@0640521a8170）：LongCat `moe_chunk_max_len` chunk 串行分支 + README「长序列请求 out of memory 处理」（根因 = Routing 负载不均 / grouped_matmul 峰值，只对 prefill 生效、有性能影响）。
- `diff 事实`（@28b8c71ac661）：Hy3 `_split_tensors` 沿 token 维分块、router 不分块（注释 "Router must see all tokens"）、prefill-only、`moe_chunk_max_len` 默认 65536。
- `diff 事实` + `维护者确认`（@2c45117）：`DeepseekMoE.forward` 的 `is_prefill` 分支走 `moe_infer_double_routing`、`all_to_all_single` 按实际 splits；「dispatch expand_tokens 按最大 shape 分配 → prefill OOM」为维护者确认。
- 溯源下探：
  - [cann-recipes-infer-issue-13-question-32-config](https://gitcode.com/cann/cann-recipes-infer/issues/13)
  - [cann-recipes-infer-pr-124-feat-support-longcat-flash-inference](https://gitcode.com/cann/cann-recipes-infer/merge_requests/124)
  - [cann-recipes-infer-pr-427-unify-the-naming-description-of-the-hy3-preview-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/427)
  - [cann-recipes-infer-issue-11-question-prefill-moe-moe-infer-double-routing](https://gitcode.com/cann/cann-recipes-infer/issues/11)
