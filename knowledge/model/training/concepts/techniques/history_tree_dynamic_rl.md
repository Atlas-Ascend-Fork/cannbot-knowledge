---
type: Concept
title: History Tree Dynamic RL（历史响应与 EAGLE3 动态投机）
description: Qwen3 RL Rollout 复用历史响应并按预热、batch bucket 和 tokens/ms 动态选择 EAGLE3 chain 草稿；说明配置、探测限制、观测信号及输出预算导致的性能比较边界。
tags:
- task.optimization
- topic.reinforcement_learning
- topic.speculative_decoding
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/features/history_tree_dynamic_rl.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/README.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/internal/train_grpo_qwen3_30b_16die_dynamic_rl.sh
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/vllm_ascend/0011-vllm_ascend-feature-dynamic_rl_proposer.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0020-verl-feature-enable_history_tree_dynamic_rl.patch
  role: implementation
created_at: '2026-10-29T04:09:06Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- a3
---

# History Tree Dynamic RL（历史响应与 EAGLE3 动态投机）

## Summary

面向 RL Rollout 长序列采样，将上一轮响应中的高 reward 片段保存为历史草稿，与独立 EAGLE3 draft model 组合。`history_tree` 只使用历史复用，`eagle3` 只使用草稿模型，`dynamic_rl` 按 batch、历史预热和在线耗时在两者之间选择。当前 EAGLE3 分支使用 chain draft，不能由补丁里存在 tree attention 推断本启动配置采用树形草稿。

## 数据与执行链路

veRL 从 Rollout batch 提取 prompt token ids、response token ids 和 token-level reward，生成稳定 prompt id，将 `history_tree_records` 同步给各 Rollout worker。`HistoryRolloutProposer` 维护按 prompt 隔离的 `FixedDraftHistoryCache`，另保留全局 fallback cache；相同 prefix 下优先保存 reward 较高的候选。第一轮没有历史响应，需要后续逐轮积累。

`DynamicProposer` 同时持有 history proposer 与 `EagleProposer`。默认 `timing_guard` 按 batch bucket 记录 tokens/ms 的 EMA：大 batch 走历史分支，小 batch 收集历史基线，再有限探测 EAGLE3；评分达到切换 margin 才换分支。差的 probe 回退并进入可增长的 cooldown，避免反复试探。

## 配置入口与边界

在 `llm_rl/qwen3/verl-mindspeed/` 准备该 recipe 的依赖和补丁，最小配置为：

```text
actor_rollout_ref.rollout.spec_method=dynamic_rl
actor_rollout_ref.rollout.eagle3_draft_model=/path/to/draft_model
actor_rollout_ref.rollout.spec_num_speculative_tokens=4
```

Qwen3-30B 16 个 NPU 逻辑设备的 GRPO 脚本为 `internal/train_grpo_qwen3_30b_16die_dynamic_rl.sh`，使用前配置 MODEL_PATH、DISTCP_PATH、TRAIN_FILE、TEST_FILE 及草稿权重。只验证历史能力时使用 `history_tree`，不要求 EAGLE3 权重；`dynamic_rl` 需要可加载的草稿模型。MoE 场景还需对应的专家并行、AllToAll/reshard 基础设置。

| 参数 | 当前默认值与作用 |
|---|---|
| `VLLM_DYNAMIC_RL_POLICY` | `timing_guard`；另支持 history_first、threshold、threshold_only |
| `VLLM_HISTORY_TREE_MAX_SPEC_REQS` | 64，历史分支参与投机的最大请求数 |
| `VLLM_DYNAMIC_RL_EAGLE_MAX_BSZ` | 8，允许考虑 EAGLE3 的 batch 上限 |
| `VLLM_DYNAMIC_RL_EAGLE_PROBE_MAX_BSZ` | 2，timing guard 主动探测上限；不能把 batch≤8 等同于都会探测 |
| `VLLM_DYNAMIC_RL_HISTORY_WARMUP_RECORDS` | 1，历史预热记录数 |
| `VLLM_DYNAMIC_RL_EAGLE_COLD_START_GUARD` | 1，历史未预热前限制冷启动 EAGLE3 |
| `VLLM_DYNAMIC_RL_COMPARE_AFTER_STEPS` | 64，bucket 内先收集的历史步数 |
| `VLLM_DYNAMIC_RL_EAGLE_PROBE_STEPS` | 8，EAGLE3 探测步数 |
| `VLLM_DYNAMIC_RL_SWITCH_MARGIN` | 1.02，切换所需评分倍率 |
| `VLLM_DYNAMIC_RL_EAGLE_ENFORCE_EAGER` | 0，当前默认允许 draft graph；设 1 使用 eager |

`VLLM_DYNAMIC_RL_HISTORY_UPPER_BSZ_EXCLUSIVE` 是历史分支上界控制，不能与 EAGLE3 的 batch 阈值混用。参数值还可能被脚本环境覆盖，应保存实际启动环境。

## 观测与可比性

开启 `VLLM_ASCEND_SPEC_TIMING=1` 后查看 dynamic_mode、dynamic_reason、dynamic_bucket、dynamic_history_ready 及两分支 tokens/ms。Rollout metrics 提供 effective_percent、effective_length、predict_times、effective_times、total_right_length，并分别统计 eagle/history 分支。先验证每轮历史同步和实际分支，再看接受长度与耗时，不能只凭配置项判定生效。

来源报告 Qwen3-30B-A3B、Deepscaler、16 个设备、prompt 1024、response 上限16384、train batch64、rollout n8、max_num_seqs64、推理 TP4、草稿长度4，取 step1–10：

| 配置 | generate_sequences / s | 整步 / s | tokens/s |
|---|---:|---:|---:|
| baseline | 1202.77 | 1511.84 | 126.86 |
| history_tree | 1048.85 | 1369.69 | 148.79 |
| dynamic_rl | 1073.45 | 1392.66 | 146.59 |
| dynamic_rl + Length-Aware | 998.65 | 1213.48 | 170.16 |

这是来源观测，本次没有硬件复测。各行平均输出长度不同，最后一行还同时开启 Length-Aware 并下发 `response_max_tokens_cap=10000`，与其他行的输出预算不同；其 +34.13% tokens/s 不能单独归因于动态投机，也不能据这组观测断言 dynamic_rl 普遍优于 history_tree。复现应控制输出预算、采样、模型/数据、并行和统计窗口，另核对 reward/评测。

## Evidence

- [history_tree_dynamic_rl.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/features/history_tree_dynamic_rl.md)（primary）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/README.md)（supporting）
- [train_grpo_qwen3_30b_16die_dynamic_rl.sh](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/internal/train_grpo_qwen3_30b_16die_dynamic_rl.sh)（implementation）
- [0011-vllm_ascend-feature-dynamic_rl_proposer.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/vllm_ascend/0011-vllm_ascend-feature-dynamic_rl_proposer.patch)（implementation）
- [0020-verl-feature-enable_history_tree_dynamic_rl.patch](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_rl/qwen3/verl-mindspeed/patches/verl/0020-verl-feature-enable_history_tree_dynamic_rl.patch)（implementation）

## Links

- [Qwen3 RL 实践](../../guides/recipes/qwen3_rl.md)
- [SAM 无模型投机](sam_speculative.md)
- [GRPO 与 DAPO](grpo_dapo.md)
