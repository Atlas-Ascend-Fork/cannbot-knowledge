---
type: Runbook
title: MoE token dispatcher 把中间张量挂 self. 属性阻止 GC：aclgraph 峰值内存虚高触发 OOM，token_combine 末尾置 None 释放
description: 在 aclgraph 下运行 expert-parallel MoE 时，若 token dispatcher 把 dispatch、expert compute、combine 之间传递的大量中间张量保存为 self 属性，长寿命实例会持续持有强引用，Python GC 无法释放，图按虚高峰值预留显存并在临界负载触发 OOM。典型对象包括路由结果、dispatch/combine 辅助信息、split 映射、MC2 mask 和 shared-expert 临时张量。修复是在各 token_combine 生成最终 hidden states 后，将已无消费者的 self 属性逐一置为 None，缩短其图内生命周期；不改变计算结果，删除置空语句即可回滚。该结论适用于 aclgraph 的 EP、MC2、all-to-all 与 shared-expert 路径，来源未提供前后峰值数字。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3158
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MoE token dispatcher 把中间张量挂 self. 属性阻止 GC：aclgraph 峰值内存虚高触发 OOM，token_combine 末尾置 None 释放

## 信号（现象）

在 [npu-graph-mode](../../concepts/techniques/npu_graph_mode.md)（aclgraph 图模式）下跑 [expert-parallel](../../concepts/parallelism/expert_parallel.md) MoE 推理，某些场景出现 NPU out-of-memory；同一路径关闭图模式 / 走 eager，或 token 规模更小时不复现或更晚复现。OOM 不来自单步计算峰值本身，而是峰值预留被拉高——即观测到的可用显存比「按当前实际活跃张量估算」应有的更少。

逐项核对是否命中：问题落在 MoE 的 dispatch → expert compute → combine 一段（[MC2](../../concepts/techniques/moe_dispatch_combine_v2.md) 融合通信路径）；且实现里 dispatcher 用类实例属性（`self.<name>`）在自身不同方法间传递中间张量。若不在这个「中间量挂对象属性、图模式按峰值预留」的组合里，本页不适用。

## 触发条件

- 框架：vLLM 的昇腾 NPU 后端（vllm-ascend），vLLM v0.10.2 量级；workload 为 MoE 模型推理走 aclgraph。
- 实现模式（触发核心）：token dispatcher 为了在同一实例的 `token_dispatch` / expert 计算 / `token_combine` 等方法之间传参，把中间张量挂成实例属性，而非用返回值 / 局部变量传递。典型属性包括 `self.output` / `self.topk_ids` / `self.topk_weights` / `self.expert_map` / `self.assist_info_for_combine` / `self.ep_recv_counts` / `self.mc2_mask`（MC2 路径），`self.expanded_row_idx`，以及 all-to-all 路径的 `self.input_splits` / `self.output_splits` / `self.num_global_tokens_per_local_expert` / `self.reversed_local_input_permutation_mapping` / `self.reversed_global_input_permutation_mapping` / `self.global_input_tokens_local_experts_indices` 等；带 shared-expert 分支时还有 `self.shared_act` / `self.shared_experts` / `self.swiglu_out_scale`。
- 图模式前提：aclgraph 下显存预留按**图内峰值**决定，任何在峰值时刻仍存活的张量都计入预留。

## 根因

实例属性对张量持有强引用。当中间张量被写进 `self.<name>`，它的生命周期被绑到 dispatcher 实例的存活期，而不是随产生它的方法返回而结束。于是即便 `token_combine` 已算出最终 `hidden_states` / `final_hidden_states` / `output`、这些中间量逻辑上已无用，Python GC 也不会回收它们——引用仍挂在长寿命对象上。

这是一个可迁移的失败签名：**把只为跨方法传参的大张量挂在长寿命对象（此处是 dispatcher 实例）的属性上，会把它们的生命周期拉长到对象存活期**；在按峰值预留内存的 NPU 图模式（aclgraph）下，这些「本该早就死掉」的张量抬高了图内峰值，直接推高显存预留、在临界场景触发 OOM。识别点单一而明确：**中间张量以 `self.` 属性持有、产出结果后无人置空**。

（边界：这属昇腾 NPU 显存 + aclgraph 峰值预留的组合放大，不是各硬件通用的框架同步 bug；泛化到「任何对象属性持有中间量都必然 OOM」是外推。）

## 修法

在各 `token_combine` 产出最终结果之后，把已不再使用的 `self.` 张量属性逐个置 `None`，解除强引用、让其立即可被回收，从而压低图内峰值内存。哪些属性该置空取决于该 dispatcher 路径实际挂了哪些中间量——原则是「该 combine 之后逻辑上已死的中间量全部置空」。三类 dispatcher 路径的参考置空集合：

```python
# MC2 路径 token_combine 末尾
self.output = None
self.assist_info_for_combine = None
self.ep_recv_counts = None
self.topk_ids = None
self.topk_weights = None
self.mc2_mask = None
self.expert_map = None
# 若走 shared_experts 分支，追加：
self.shared_act = None
self.shared_experts = None
self.swiglu_out_scale = None
```

```python
# 另一 dispatcher 路径 token_combine 末尾
self.expert_map = None
self.topk_weights = None
self.topk_ids = None
self.expanded_row_idx = None
```

```python
# all-to-all 路径 token_combine 末尾
self.input_splits = None
self.output_splits = None
self.num_global_tokens_per_local_expert = None
self.topk_weights = None
self.reversed_local_input_permutation_mapping = None
self.reversed_global_input_permutation_mapping = None
self.global_input_tokens_local_experts_indices = None
```

- 改动只在 dispatcher 文件、纯新增置空语句（无删除、无逻辑改动），风险低；correctness 不受影响——被置空的属性到下一次 forward 会被重新赋值，置空发生在它们本轮已无消费者之后。
- rollback：删掉这些置空语句即回到旧行为；无状态迁移、无接口变更。
- 收益方向明确（释放中间量、降峰值、修 OOM），但 source 未给 before→after 的具体显存数字或独立复测，故不引用峰值内存量化收益。

## 参考实现及其约束

参考实现见 vllm-ascend 的 `vllm_ascend/ops/moe/token_dispatcher.py` 三个 dispatcher 类的 `token_combine`（PR 合并态）。上面列出的具体属性名、每类各置空哪些，是**该参考实现的中间量集合**，随实现演进而变——它是那份代码的细节，不是本失败签名的边界。可迁移的是判断法则本身：图模式 MoE dispatcher 里凡「中间张量挂 `self.` 属性、combine 后无人置空」，就核查是否需在产出末尾显式置 `None`。

## 相关经验

- 同一 PR 另见 [profile-run 不走 MC2 路径致 NPU 峰值内存低估、运行期 OOM](moe_optimization_silently_disabled_decode.md)：与本页同源于该 OOM 修复的另一分支，属「profiling 阶段与运行期路径不一致导致显存低估」的失败签名。
- 峰值内存视角的 MoE prefill OOM 处置见 [MoE 长序列 prefill 峰值显存 / OOM](moe_prefill_oom_peak_memory.md)（专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing）。

## Evidence

- 合并态 diff：三个 dispatcher 类 `token_combine` 末尾各追加 `self.<attr> = None` 置空，与「实例属性持有阻止 GC → 图模式峰值虚高 → OOM」的根因一致；改动 +24 行 / 0 删除，仅 `token_dispatcher.py`。
- 无 before→after 峰值内存数字或独立复测，收益仅为方向性。
- 溯源下探：
  - [vllm-ascend-pr-3158-bugfix-fix-oom-in-aclgraph](https://github.com/vllm-project/vllm-ascend/pull/3158)（mergeCommit `69509bcdd693dc6653db81648d4775af24ceb2b2`）

<!-- cannbot:related:start -->
## 相关

- [MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置](moe_prefill_oom_peak_memory.md)（`related`）：［expert-parallel］(../../concepts/parallelism/expert_parallel.md) MoE 模型在**长序列 prefill** 阶段 device OOM（`EL0004 Failed to allocate memory` / `out of memory`），常发生在 MoE 的 `grouped_matmul` 或 dispatch 展开处；同配置换短输入 / 小序列不复现。；实例属性对张量持有强引用。当中间张量被写进 `self.<name>`，它的生命周期被绑到 dispatcher 实例的存活期，而不是随产生它的方法返回而结束。于是即便 `token_combine` 已算出最终 `hidden_states` / `final_hidden_states` / `output`、这些中间量逻辑上已无用，Python GC 也不会回收它们——引用仍挂在长寿命对象上。；两张卡分别覆盖长输入 OOM 现象与对象属性延寿机制，可用于区分真实单步峰值和图模式生命周期虚高。
- [profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影响峰值的路径/均衡步（MC2 通信 / force_load_balance）](profile_run_peak_memory_underestimate_untraversed_path.md)（`related`）：实例属性对张量持有强引用。；profiling 阶段没有实际走一遍某条会额外吃 NPU 内存的路径、或没有触发某个会改变显存分布的均衡步，导致峰值被低估，运行期真实占用超出预留而 OOM。两卡是 aclgraph MoE OOM 排障中必须区分的两条机制：运行期中间张量滞留与 profiling 漏覆盖。
<!-- cannbot:related:end -->
