---
type: Runbook
title: profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影响峰值的路径/均衡步（MC2 通信 / force_load_balance）
description: failure_signature 动态页：推理引擎用 profile_run / dummy forward 估计昇腾 NPU 推理期峰值显存并按估计值预留 device 显存 / KV cache 容量（aclgraph NPU 图模式尤其依赖此预留），若 profiling 阶段没有实际走一遍所有会拉高真实峰值的路径或均衡步，峰值被低估、运行期 device OOM。根本判据：profile_run 必须把所有会额外吃 NPU 内存的路径和会改变显存分布的均衡步都在 profiling 阶段实际跑一遍。汇聚两个具体信号：(1) profiling 不走 MC2 融合 MoE dispatch/combine 通信（npu_moe_distribute_dispatch/combine）路径 → 漏计 MC2 通信 buffer 显存 → aclgraph 下 MoE 运行期 OOM；修法是在 profile_run 里当 _select_moe_comm_method(mc2_tokens_capacity) == MoECommType.MC2 时补跑一次经 MC2 的 _dummy_run 完成初始化 / 内存分配，SOC/world_size 判据由选路函数内部承担。(2) MoE force_load_balance（仅 profile run 激活、用 torch.randint_like 随机重写 topk_ids 把 token 均匀铺到所有 expert 避免堆到单 rank）曾因 aclgraph 图捕获模式不支持 torch.randint_like 而被 self.use_aclgraph 门控关掉 → profile 显存不反映均衡分布 → OOM；修法是随算子可用拆掉 aclgraph 门控让 force_load_balance 图模式生效。参考实现 vllm-ascend（model_runner_v1.py profile_run、fused_moe.py AscendUnquantizedFusedMoEMethod）。关联 expert-parallel EP、moe-dispatch-combine-v2、npu-graph-mode aclgraph、eplb。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/3158
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/pull/4366
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# profile_run 峰值显存低估致运行期 OOM：profiling 未实际走一遍所有影响峰值的路径/均衡步（MC2 通信 / force_load_balance）

## 适用场景

推理引擎在启动时用一次占位前向（`profile_run` / dummy forward）**估计推理期 NPU 峰值显存**，再按这个估计值预留 device 显存 / 划定 KV cache 容量；[NPU 图模式（aclgraph）](../../concepts/techniques/npu_graph_mode.md) 尤其依赖这个估计值预留显存。这类 failure signature 的共性是：**profiling 阶段没有实际走一遍某条会额外吃 NPU 内存的路径、或没有触发某个会改变显存分布的均衡步，导致峰值被低估，运行期真实占用超出预留而 OOM**。

命中判据：

- 症状是**运行期 device OOM**（`out of memory` / 显存分配失败），而非编译期 / 首步冷启动个例；
- 引擎按 `profile_run` 估出的峰值来预留显存 / 定 KV cache（vLLM 系、aclgraph 预留是典型）；
- workload 是 [MoE / EP](../../concepts/parallelism/expert_parallel.md)，峰值显存对**通信路径**（dispatch/combine 通信 buffer）和**专家负载分布**（token 是否堆到单卡）高度敏感；
- 换小序列 / 小 world_size / 关掉某条通信或均衡路径就不复现——提示峰值来自某条 profiling 没覆盖到的路径。

根本判据（可迁移，独立于具体框架）：**profile_run 只有把「所有会拉高真实峰值的路径和分布」都在 profiling 阶段实际跑一遍，估计值才可信**。任何「只在特定通信 / 算子路径才发生的额外 NPU 内存分配」，或「只有做了负载均衡后才呈现的真实显存分布」，若没在 profiling 里被主动触发，就会被漏计 → 峰值低估 → 运行期 OOM。下面两个具体信号是这条判据的两种表现。

## 信号一：profiling 不走 MC2 通信路径 → 漏计 MC2 通信 buffer → 峰值低估 OOM

### 信号（现象）
aclgraph 下 MoE 推理**运行期 OOM**；模型经 [MC2 融合 MoE dispatch/combine 通信](../../concepts/techniques/moe_dispatch_combine_v2.md)（`npu_moe_distribute_dispatch/combine`）做专家 token 分发/回收。

### 触发条件与根因
`profile_run` 用一次 dummy 前向精确估计推理期最大 NPU 内存。但 MC2 的 dispatch/combine 通信自带**通信 buffer**，会额外占用 NPU 内存；而首次 dummy 前向**不一定走到 MC2 路径 / 不触发 MC2 的初始化与内存分配**。于是 MC2 那部分显存没被 profile 计入 → 峰值估计偏低 → 引擎按低估值预留 → 真实运行时经 MC2 通信超出预留 → OOM。

### 修法
在 `profile_run` 的常规 dummy 前向之后，**当选路器判定本部署会走 MC2 时，补跑一次经 MC2 的 dummy_run**，把 MC2 的初始化 / 内存分配提前到 profiling 阶段，使峰值估计把 MC2 通信占用计入：

```python
# MC2 will consume additional NPU memory.
# Therefore, we need to run the MC2 path once here to complete its initialization,
# allowing vLLM to correctly estimate the maximum memory required.
if self._select_moe_comm_method(
        self.mc2_tokens_capacity,
        with_prefill=True) == MoECommType.MC2:
    self._dummy_run(self.mc2_tokens_capacity)
```

门控只依赖选路器（是否会选 MC2）本身：以 `mc2_tokens_capacity` 询问选路函数是否会选 MC2 通信路径，只有会选 MC2 时才补跑。**是否走 MC2 的 SOC 版本 / world_size 判据由选路函数内部承担**，修法本身不再另写 SOC/world_size 条件（参考实现中一条 review 建议对 A2 额外加 `world_size >= 16` 显式条件，合并态未采纳）。

## 信号二：profiling 的 force_load_balance 被图模式门控关掉 → 峰值不反映均衡分布 → OOM

### 信号（现象）
MoE 层在 **profile run** 下、且图模式为 aclgraph 时，profiling 估出的显存不反映负载均衡后的真实分布，运行期 OOM。

### 触发条件与根因
`force_load_balance` 是一段刻意的 expert 负载均衡实现，**仅在 profile run 时激活**（源码注释：`this is a naive implementation for experts load balance so as to avoid accumulating too much tokens on a single rank. currently it is only activated when doing profile runs.`）。其作用：profile run 时把 token 随机均匀铺到所有 expert，避免 token 在单个 rank 上堆积——否则 profile 出的显存不反映均衡分布，实际运行会 OOM。

该均衡靠 `torch.randint_like(topk_ids, 0, global_num_experts)` 随机重写 `topk_ids` 实现。历史约束：**aclgraph 图捕获模式历史上不支持 `torch.randint_like`**，于是 force_load_balance 被 `self.use_aclgraph` 门控在图模式下**关掉**（原判据 `if enable_force_load_balance and not self.use_aclgraph:`）。图模式下拿不到负载均衡 → profile run 的显存判断失真 → 运行期 OOM。

### 修法
一旦所依赖的随机 op（此处 `torch.randint_like`）在图模式下**已可用**，拆掉这道 aclgraph 门控，让 force_load_balance 在图模式下也生效：

- `apply()` 判据由 `if enable_force_load_balance and not self.use_aclgraph:` 改为 `if enable_force_load_balance:`；
- 同时清理已成死代码的 `self.use_aclgraph` 计算与相关 import / 注释。

**评估「MoE profile run 是否 OOM」时须确认负载均衡这一步在当前图 / eager 模式下确实生效**：如果它被某执行模式的算子支持缺口静默关掉，profile 的显存就会失真。这条与「[draft dummy_run 误带 profile 语义触发随机专家路由](../precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)」是一体两面——force_load_balance 的随机专家在**真正的 profile run 里有意且正确**（均摊负载、压出真实峰值），只有当它被误带进「会影响真实输出的路径」（如投机 draft 产草稿）时才有害。

## 参考实现及其约束

- 信号一参考实现：vllm-ascend（vLLM 昇腾 NPU 后端，vLLM v0.10.2），`vllm_ascend/worker/model_runner_v1.py` 的 `profile_run`，追加 MC2 dummy_run（合并态 +8/-0）。`mc2_tokens_capacity`、`_select_moe_comm_method`、`MoECommType.MC2` 为该参考实现的具体接口；「是否走 MC2 由选路函数内部按 SOC/world_size 定」属该实现约定，不是技术本身的限制。source 未给 before→after 显存数字。
- 信号二参考实现：vllm-ascend（vLLM v0.11.0），`vllm_ascend/ops/fused_moe/fused_moe.py` 的 `AscendUnquantizedFusedMoEMethod`，拆 aclgraph 门控（`fused_moe.py` +2/-16）。`self.use_aclgraph` 门控、`torch.randint_like` 支持缺口是该参考实现的具体机制；「aclgraph 不支持 `torch.randint_like`」是历史事实、随算子支持推进而失效，非永久约束。PR 声称过 e2e & ut，未给 before→after 显存数字。
- 可迁移面：两条信号的**思想**（profiling 必须实际走一遍所有影响峰值的路径 / 均衡步，否则峰值低估 OOM）通用；但「MC2 通信 buffer」「force_load_balance 挂在哪个标志、靠哪个随机 op」是 vllm-ascend 自有的昇腾 fused-MoE 机制，落地他框架时须自行核对本框架 profile 路径漏了哪些额外分配 / 均衡步。

## 相关经验

- MoE 长序列 prefill 峰值显存 / OOM（专家负载不均 + dispatch 中间量放大；分块 / EPLB / double-routing 处置）：[MoE 长序列 prefill 峰值显存 / OOM](moe_prefill_oom_peak_memory.md)。
- profile 语义误用的另一面（draft dummy_run 误带 profile 随机专家路由拉低 accept rate）：[MoE + 投机解码：draft dummy_run 误带 profile-run 语义](../precision/mtp_draft_dummy_run_in_profile_run_random_experts.md)。
- perfect_eplb profiling 上界与均衡确诊：[perfect_eplb profiling 上界](../../optimizations/experience/rules/perfect_eplb_profiling_upper_bound.md)。

## Evidence

- 信号一（`profile_run` 追加 MC2 dummy_run）：合并态 diff 事实 @merge sha `69509bcdd693dc6653db81648d4775af24ceb2b2`（merged 2025-09-26），`vllm_ascend/worker/model_runner_v1.py`。根因（MC2 通信额外吃显存 → 首次 dummy 前向不一定走 MC2 → profile 低估 → 运行期 OOM）由作者披露、diff 印证；A2 加 `world_size >= 16` 的 review 建议合并态未采纳。source 未给显存数字。
- 信号二（拆 aclgraph 门控让 force_load_balance 图模式生效）：合并态 diff 事实 @merge sha `5b1a7514eb101c69e4925c22d83d02f3219f2d20`（merged 2025-11-24），`vllm_ascend/ops/fused_moe/fused_moe.py`（+2/-16）。force_load_balance 用途、「仅 profile run 激活」、「aclgraph 历史不支持 `torch.randint_like` 故被门控关闭」均为存活 / 删除注释原文，OOM 与支持缺口的因果由被删注释显式陈述、非推断。source 未给显存数字。
- 溯源下探：
  - [vllm-ascend-pr-3158-bugfix-fix-oom-in-aclgraph](https://github.com/vllm-project/vllm-ascend/pull/3158)
  - [vllm-ascend-pr-4366-bugfix-moe-enable-force-load-balance-in-aclgraph](https://github.com/vllm-project/vllm-ascend/pull/4366)

<!-- cannbot:related:start -->
## 相关

- [MoE token dispatcher 把中间张量挂 self. 属性阻止 GC：aclgraph 峰值内存虚高触发 OOM，token_combine 末尾置 None 释放](moe_token_dispatcher_self_attr_oom_aclgraph.md)（`related`）：实例属性对张量持有强引用。；profiling 阶段没有实际走一遍某条会额外吃 NPU 内存的路径、或没有触发某个会改变显存分布的均衡步，导致峰值被低估，运行期真实占用超出预留而 OOM。两卡是 aclgraph MoE OOM 排障中必须区分的两条机制：运行期中间张量滞留与 profiling 漏覆盖。
- [MoE 长序列 prefill 峰值显存 / OOM：专家负载不均 + dispatch 中间量放大；分块 / 均衡 / double-routing 处置](moe_prefill_oom_peak_memory.md)（`related`）：［expert-parallel］(../../concepts/parallelism/expert_parallel.md) MoE 模型在**长序列 prefill** 阶段 device OOM（`EL0004 Failed to allocate memory` / `out of memory`），常发生在 MoE 的 `grouped_matmul` 或 dispatch 展开处；同配置换短输入 / 小序列不复现。；根本判据（可迁移，独立于具体框架）：**profile_run 只有把「所有会拉高真实峰值的路径和分布」都在 profiling 阶段实际跑一遍，估计值才可信**。任何「只在特定通信 / 算子路径才发生的额外 NPU 内存分配」，或「只有做了负载均衡后才呈现的真实显存分布」，若没在 profiling 里被主动触发，就会被漏计 → 峰值低估 → 运行期 OOM。下面两个具体信号是这条判据的两种表现。；焦点给出长序列 prefill 的 OOM 现象，目标说明 profile_run 漏跑高峰路径或分布会低估峰值并导致运行期 OOM。
<!-- cannbot:related:end -->
