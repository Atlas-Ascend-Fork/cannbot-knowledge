---
type: Concept
title: GRPO / DAPO（组相对策略优化 RL 算法）
description: GRPO（Group Relative Policy Optimization，组相对策略优化）是 DeepSeek-R1 RL 训练采用的核心策略梯度算法：它去掉 PPO 的 critic（价值网络），改用「同一 prompt 采样一组（group）rollout，用组内奖励的相对高低估计 advantage」。少了独立 value model，省去其前反向与显存，特别契合 671B 级大模型的全共卡 RL 部署。本页讲清 GRPO 的 rollout → reward → advantage → 策略更新 数据流与其 on-policy 性质，并把 DAPO 作为同族变体先占位（后续 Qwen3 recipe 会丰富 DAPO 细节）。本页以 deepseek-r1-rl 实践（verl + MindSpeed + vLLM-Ascend，Atlas A3 128 卡）中 GRPO 的真实用法为据。 > 本页是 GRPO/DAPO 算法的 唯一 canonical 页：讲算法机制本身。verl 框架的单/多控制器调度、D2D 数据流加速、训推切换 reshard 等 工程优化 归 verl 与 deepseek-r1-rl，本页只在与 GRPO 算法语义耦合处（如 on-policy 免计算 old_log_prob）引用。 MindSpeed-RL 把 GRPO/DAPO/PPO 做成继承 RayBaseTrainer 的 Ray 共卡 trainer（grpo/dapo/ppo_trainer_hybrid），损失按 (stage,role) 注册 LossFuncFactory、组优势 compute_group_norm_advantage_return 组内 z-score；DAPO kl_loss≡0、PPO 用 CriticWorker+GAE+apply_kl_penalty；DPO 委托 mindspeed_llm 离线 DPOTrainer。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# GRPO / DAPO（组相对策略优化 RL 算法）

## Summary

GRPO（Group Relative Policy Optimization，组相对策略优化）是 DeepSeek-R1 RL 训练采用的核心策略梯度算法：它**去掉 PPO 的 critic（价值网络）**，改用「**同一 prompt 采样一组（group）rollout，用组内奖励的相对高低估计 advantage**」。少了独立 value model，省去其前反向与显存，特别契合 671B 级大模型的全共卡 RL 部署。其数据流为 **rollout → reward → advantage → 策略更新**，并具备 **on-policy** 性质。**DAPO**（GRPO 同族变体）在此骨架上叠加解耦 clip 上下界 / token-level 重要性采样 / 动态样本过滤等改动。GRPO 在 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md) 实践（[verl](../frameworks/verl.md) + MindSpeed + vLLM-Ascend，Atlas A3 128 卡）中的真实用法见下文。

> GRPO/DAPO 讲算法机制本身。verl 框架的单/多控制器调度、D2D 数据流加速、训推切换 reshard 等 *工程优化* 见 [verl](../frameworks/verl.md) 与 [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)；与 GRPO 算法语义耦合处（如 on-policy 免计算 old_log_prob）在下文相应小节说明。

## 在 RL 训练系统中的位置

DeepSeek-R1 的每一步 GRPO 训练拆成三个计算密集阶段：

> DeepSeek R1 的每一步训练可大致分为三个计算密集的阶段：推理生成完整问答数据（rollout/generate）-> 参考模型计算参考概率分布（ref）-> 训练模型计算 loss 并反向更新（update）。

这正是 GRPO 数据流的工程落地：rollout 产出一组响应、ref 提供 KL 正则所需的 $\pi_{ref}$ 分布、update 用组内相对 advantage 更新策略。三阶段对 671B 模型都吃资源，故本实践对 actor / rollout / ref **三模型全共卡、分时复用**部署。整套 RL 优化分四个方面（模型间调度 / 训推切换 / 训练 / 推理）展开：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image2.png" width="55%"></p>
<p align="center"><sub>图：基于 verl 的 DeepSeek-R1 RL 训练四方面优化总览（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·verl 适配和优化实践总览）</sub></p>

verl 框架本身「结合单控制器（控制流）与多控制器（计算流）优势，简化了 RL 算法（如 PPO、GRPO）实现」（源文档框架介绍表），GRPO 即作为其内置算法之一被本实践驱动。

## GRPO 数据流：rollout → reward → advantage → update

### Rollout（采样一组响应）

对每个 prompt $q$，由当前策略 $\pi_{\theta_{old}}$ 采样 **一组 $G$ 个响应** $\{o_i\}_{i=1}^{G}$（recipe 中 `n_samples = 16`）。这是 GRPO「组」的来源——后续 advantage 在这 $G$ 个响应内做相对比较。推理生成由 vLLM-Ascend 承担，在长序列场景下耗时常占 RL 一步总耗时的近一半甚至 80%+。

> GRPO 的 rollout 输入只有 prompt（不含 response），且其 `batch_size` **没有**经过 `n_sample` 倍数放大（放大发生在生成出 $G$ 条响应之后）——这是源文档 §3.1.4 解释「gen 任务下发数据量远小于训练侧」的原因之一，也间接刻画了 GRPO 组采样的数据形状。

### Reward（逐响应打分）

每条响应 $o_i$ 经奖励函数得到标量奖励 $r_i$（recipe 用 deepscaler / gsm8k 等带可验证答案的数学数据集，走规则/答案匹配类 reward_score）。reward 阶段在 RL 一步里耗时很小（源文档性能表 `reward (s)` 列：真实权重 5.0s、随机权重 13.7s）。

### Advantage（组内相对优势，去 critic 的核心）

GRPO **不训练 value 网络**：一组 $G$ 条响应的奖励 $\{r_i\}$ 直接做组内归一化，得到每条响应的 advantage $\hat{A}_i$（组内相对优势，组均值附近为基线），再广播到该响应的每个 token。这一步在系统里极轻量（源文档性能表 `adv (s)` 列仅 **0.21s / 0.188s**），与 PPO 需 value model 前向算 GAE 形成鲜明对比——**省掉 critic 正是 GRPO 在大模型 RL 上省资源的关键**。

### 策略更新（update，带 clip + KL 正则）

用组内 advantage 做策略梯度更新。GRPO 目标函数（源文档 §5.2 配图，逐 token 形式）：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/figures/deepseek_figures/image21.png" width="72%"></p>
<p align="center"><sub>图：GRPO 目标函数——min(ratio·Â, clip(ratio,1±ε)·Â) − β·D_KL[π_θ‖π_ref]；on-policy 下重要性比 ratio 分子分母数值相等（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md">DeepSeek-R1 RL 训练优化文档</a>·old_log_prob 免计算）</sub></p>

目标对每个 prompt 的 $G$ 条响应、每条响应的每个 token 求平均，单 token 项由三部分组成：

- **重要性比裁剪项** $\min\!\big(\rho_{i,t}\hat{A}_{i,t},\ \mathrm{clip}(\rho_{i,t},1{-}\varepsilon,1{+}\varepsilon)\hat{A}_{i,t}\big)$，其中重要性比 $\rho_{i,t}=\dfrac{\pi_\theta(o_{i,t}\mid q,o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}\mid q,o_{i,<t})}$；
- **KL 正则项** $-\beta\,\mathbb{D}_{KL}\big[\pi_\theta\,\|\,\pi_{ref}\big]$，把更新后的策略拉回参考模型 $\pi_{ref}$ 附近——这正是三阶段里 **ref 阶段计算参考概率分布**的用途。

advantage $\hat{A}_{i,t}$ 由上一步组内相对优势给出（同响应所有 token 共享），无 value model 参与。

## on-policy 性质：old_log_prob 与 log_prob 数值相等

GRPO 是 **on-policy** 算法：每一步 update 用的就是产出这批 rollout 的同一份模型参数，没有跨步骤复用旧数据。由此源文档 §5.2 给出一个直接的工程优化——**old_log_prob 免计算**：

> 对于 GRPO 这类 on-policy 训练算法，其 old_log_prob 计算结果与 update_actor 前向计算所得的 log_prob 数值相同（因为训练模型参数一致），因此可直接使用 `log_prob.detach()` 替代 old_log_prob，从而省去一次训练模型前向计算的耗时。

即图中 $\pi_{\theta_{old}}$ 与 $\pi_\theta$ 在 on-policy 下数值相等（图内红框标注「on-policy 中与分子数值相等」），重要性比 $\rho_{i,t}\equiv 1$，故 `old_log_prob` 无需单独前向，可由 update 阶段的 `log_prob.detach()` 直接得到。recipe 为 verl 补充了该特性：

```shell
# 将 recompute_old_log_prob 置 False 即启用 old_log_prob 免计算（on-policy 专用）
config.actor_rollout_ref.actor.recompute_old_log_prob = False
```

性能表的 `old_log_prob (s)` 列因此恒为 **0**——这一项被完全消除。需注意该免计算严格依赖 on-policy 假设：源文档 §3.2.4 明确「当前只支持 GRPO on-policy，off-policy 可能需要 batch_size 方面的细节调整」，即 D2D TensorCache 数据流加速同样建立在 GRPO on-policy 前提上。

## DAPO（GRPO 同族变体）

DAPO（Decoupled Clip & Dynamic Sampling Policy Optimization）是 GRPO 的同族改进算法，沿用「组采样 + 去 critic 的组内相对 advantage」骨架，在 GRPO 基础上叠加四项改动以缓解长序列 RL 的熵塌缩与梯度信号稀疏。Qwen3 235B/32B RL 实践（[qwen3-rl](../../guides/recipes/qwen3_rl.md)）按以下 DAPO 配置实测（启动脚本 `train_dapo_qwen3_{235b_128die,32b_32die}_true_weight.sh`）：

1. **解耦 clip 上下界（Clip-Higher）**：把对称裁剪拆成独立上下界 `clip_ratio_low=0.2` / `clip_ratio_high=0.28`——抬高上界给低概率 token 更多探索空间、抑制熵塌缩；另设 dual-clip 常数 `clip_ratio_c=10.0`。
2. **token-level 重要性采样**：`rollout_is_threshold=2.0`（`rollout_is_threshold_lower=null`，无下界），在 token 粒度裁剪重要性比。
3. **token-level PG Loss**：`loss_agg_mode="token-mean"`，按 token 而非按样本聚合策略梯度损失（长 response 不被样本级平均稀释）。
4. **动态样本过滤**：`algorithm.filter_groups.enable=True`（`metric=acc`，`max_num_gen_batches=10`），去除组内 reward 全为 0 或全为 1 的「零梯度」样本组——这类组的组内相对 advantage 恒为 0、对更新无贡献；过滤后首个 step 需多做 batch 推理补足有效样本（235B 实测首 step 做 2 个 batch 推理）。

DAPO 同时关闭 KL 惩罚项（`use_kl_loss=False`，对比 GRPO 脚本的 `use_kl_loss=True`）。以上均为 verl 的 `actor_rollout_ref.actor.*` / `algorithm.*` 配置项，不改 GRPO 的「组相对、去 critic」骨架即可切换。具体性能（235B DAPO 41.88 TPS/卡、32B DAPO 叠 SAM/npugraph_ex 首步 4562→3261）见 [qwen3-rl](../../guides/recipes/qwen3_rl.md)。

DAPO 与 GRPO 均为「组相对、on-policy」族，落到 verl 上都靠 [verl](../frameworks/verl.md) 的单控制器调度驱动 rollout/ref/update 三阶段。

## 与 PPO 的关键差异

| 维度 | PPO | GRPO（本页） |
|------|-----|--------------|
| value/critic 网络 | 需要独立 value model 算 GAE | **无 critic**，组内相对奖励直接估 advantage |
| advantage 来源 | value model 前向 + GAE | 同 prompt 一组 $G$ 响应的奖励组内归一化 |
| 系统开销 | 多一个模型的前反向 + 显存 | adv 阶段仅 ~0.2s（性能表），省 critic 资源 |
| 重要性比 | 跨更新步可 off-policy 复用 | on-policy，$\rho\equiv1$，old_log_prob 可免算 |
| 大模型适配 | critic 加剧 671B 共卡显存压力 | 全共卡 rollout/ref/update 三模型分时复用 |

## MindSpeed-RL 实现

以上为 verl（cann-recipes-train）侧用法。[mindspeed-rl](../frameworks/mindspeed_rl.md) 在原生 `mindspeed_rl` 代码线里把 GRPO / DAPO / PPO 各做成一个独立的 Ray 共卡 trainer（`grpo_trainer_hybrid.py` / `dapo_trainer_hybrid.py` / `ppo_trainer_hybrid.py`，均继承 `RayBaseTrainer`），三者复用同一套 actor / reference / reward worker 与 TransferDock 经验队列，只在「优势估计 + 策略损失 + 编排环节」上分叉。策略损失按 `(stage, role)` 注册进 `LossFuncFactory`——`ray_grpo` / `ray_dapo` / `ray_ppo` 各自的 `actor` 损失即对应算法实现。DPO 是例外，不走共卡 rollout（见末节）。

### 组内归一化优势（GRPO/DAPO 共用，去 critic）

GRPO/DAPO 的 `adv_estimator="group_norm"`，优势由 `compute_group_norm_advantage_return` 给出：把一组奖励 reshape 成 `(-1, n_sample_per_prompt)`，组内做 z-score 归一 `(scores - mean) / (std + 1e-6)`，再按响应长度广播回每个 token 并乘 `eos_mask`。整组只用奖励标量、无 value 网络参与，这是「去 critic」的落点。PPO 则 `adv_estimator="gae"`，走 `compute_gae_advantage_return`——需 critic 产出的 `values` 加 `gamma`/`lam` 做 GAE，故 PPO trainer 多挂一个 `CriticWorker`（`compute_values` → `update_critic`），正是 GRPO/DAPO 相对 PPO 省下的那个模型。

### 三条策略损失的分叉点

三者策略梯度主项同形：`ratio = exp(log_prob - old_log_prob)`，`pg = masked_mean(max(-adv·ratio, -adv·clip(ratio)))`。`old_log_prob` 为 None 时一律取 `log_prob.detach().clone()` 使 `ratio ≡ 1`——这是 on-policy 免算 old_log_prob 的入口（见下）。差异在裁剪与正则：

- **GRPO**（`_compute_grpo_policy_loss`）：对称裁剪 `clip_ratio=0.2`；KL 正则**进损失**——`pg_loss = pg + kl_mean_loss·kl_ctrl.value - entropy_coeff·entropy`，其中 `kl_mean_loss` 由 `compute_kl_penalty(log_prob, ref_log_prob)` 按 token-mean 得到。这与本页上方 verl 侧 GRPO 目标函数图（`min(...) − β·D_KL[π_θ‖π_ref]`）逐项对应，β 即 `kl_ctrl.value`，由 `FixedKLController` / `AdaptiveKLController` 给定。
- **DAPO**（`_compute_dapo_policy_loss`）：解耦上下界裁剪 `clamp(ratio, 1-clip_ratio_low, 1+clip_ratio_high)`（`clip_higher_enable=true` 时取 `0.2`/`0.28`，关闭则退回对称 `clip_ratio`）；`token_level_loss=true` 走 token-mean（长 response 不被样本级平均稀释），关闭则退回 seq-mean-token-mean（先按序列做 token 均值再对序列求均）。DAPO **不带 KL 项**——`kl_loss` 恒为 0、不消费 `ref_log_prob`，`pg_loss = pg - entropy_coeff·entropy`，与 verl 侧 DAPO `use_kl_loss=False` 同义。
- **PPO**（`_compute_ppo_policy_loss`）：对称裁剪 0.2、actor 损失同样不含 KL；KL 改在奖励侧折叠——`apply_kl_penalty` 把 `token_level_rewards = rm_score - β·KL(old_log_prob, ref_log_prob)` 后再做 GAE。所以 PPO 的 KL 作用在 reward、GRPO 的 KL 作用在 loss。

### 一轮迭代的编排（fit 循环）

GRPO 的 `fit` 把组采样数据流逐阶段下发 TransferDock：`generate_sequences`（vLLM 推理生成一组 $G$ 响应）→ `compute_rm_score`（规则奖励，见 [rule-reward-verifier](rule_reward_verifier.md)；数学题走 `math_dapo.compute_score` 的 boxed 答案匹配，命中 +1 否则 -1）→ `compute_advantage`（group_norm，由 `compute_advantage.remote()` 派一个单独 CPU ray task 算）→ `compute_ref_log_prob`（reference 给 KL 正则的 $\pi_{ref}$）→ `compute_log_prob`（old，可跳过）→ `update`。PPO 在 advantage 前插 `compute_values`、update 阶段并做 `update_critic`（源码里 `update_critic` 紧接 advantage、在 `update_actor` 之前）。

**on-policy 免算 old_log_prob**：`set_actor_log_prob_skip_flag` 在 `global_batch_size × n_samples_per_prompt == mini_batch_size` 且 `epochs == 1` 时置 `skip_actor_log_prob=True`，fit 循环据此跳过 `compute_log_prob`，损失里 `old_log_prob=None` 触发 `ratio≡1`。这是原生侧对应 verl `recompute_old_log_prob=False` 的同款 on-policy 优化——两条线机制一致、开关入口不同（一个是显式 config flag，一个按 batch 形状自动判定）。

### DAPO 动态采样过滤

DAPO trainer 的 `dynamic_sampling` 落地「过滤零梯度组 + 动态补采」：`filter_groups_enable=true` 时，每生成一个 batch 先 `enter_infer_mode`，由 `DynamicSampling`（按 metric 剔除组内奖励全 0 或全 1 的样本组——其 group_norm 优势恒 0、对更新无贡献）统计 `num_prompt_in_batch = 有效条数 // n_samples_per_prompt`；不足 `filter_groups_train_batch_size` 且 `num_gen_batches < filter_groups_max_batches`（`-1` 表不限）时 `continue` 再采一个 batch，超出上限则 `raise ValueError('Generated too many')`，凑够后才 `exit_infer_mode` 进入训练。这与本页上方 verl 侧 `algorithm.filter_groups.enable` 的「首 step 多做 batch 推理补足有效样本」是同一机制。DAPO 另有超长惩罚（`overlong_buffer_enable` + `rollout_max_tokens` / `overlong_buffer` / `overlong_buffer_penalty_factor`）在奖励侧对接近/超出长度上限的响应做软惩罚，缓解长序列截断噪声。

### 与 verl 侧的对照

| 维度 | verl（cann-recipes-train，本页上方） | MindSpeed-RL 原生 |
|---|---|---|
| 调度 | 单控制器(控制流)+多控制器(计算流)，D2D TensorCache | Ray 共卡 trainer + TransferDock 经验队列 |
| GRPO KL | 目标函数内 `β·D_KL`（图示） | 损失内 `kl_ctrl.value·kl_mean_loss`（同义） |
| DAPO KL | `use_kl_loss=False` | `kl_loss≡0`，不消费 ref_log_prob（同义） |
| on-policy old_log_prob | `recompute_old_log_prob=False` 显式开关 | `skip_actor_log_prob` 按 batch 形状自动判定 |
| 动态过滤 | `algorithm.filter_groups.enable` | `filter_groups_enable` + `DynamicSampling` worker |
| PPO/DPO | 文档聚焦 GRPO/DAPO | 额外原生支持 PPO(带 critic+GAE) 与离线 DPO |

原生侧实测端到端 tps（A3 单卡口径需 ×2）：GRPO Qwen2.5-7B 220 / Qwen3-8B 252 / DeepSeek-R1-671B(GBS384·n32) 210；DAPO Qwen3-32B 140 / Qwen2.5-32B(30720 tok,关动态采样) 108；PPO Qwen2.5-32B(GBS128·n8) 74。

### DPO：离线偏好，不走共卡 rollout

DPO 是四算法里的异类：`cli/train_dpo.py` 不挂 actor/rollout/reward/critic，直接委托 `mindspeed_llm.tasks.posttrain.dpo.DPOTrainer`，在成对偏好数据（`is_pairwise_dataset`，chosen/rejected 两条）上做纯 Megatron 训练，对照 reference 模型优化偏好对数比——无 rollout、无 vLLM、无组采样。它复用 MindSpeed-RL 的数据预处理与权重转换栈，但不落在「rollout→reward→advantage→update」这条在线 RL 数据流上。原生侧 DPO 实测 Qwen3-30B-A3B 全参 A2 2.78 / A3 7.19 samples/s。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_rl/deepseek_rl_train_optimization.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_rl/deepseek_rl_train_optimization.md)（§1.1 框架表「verl 简化 PPO/GRPO 实现」；§1.2.1 rollout/ref/update 三阶段全共卡；§1.3 + image2 四方面优化总览；§3.1.4 GRPO gen 输入不被 n_sample 放大；§3.2.4「只支持 GRPO on-policy」；§5.2 + image21 GRPO 目标函数与 old_log_prob 免计算）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/deepseek/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/README.md)（DeepSeek-V3-671B / Atlas A3 128 卡 / GBS 512 / n_samples 16 / deepscaler 数据集 / 120 TPS 的 GRPO RL 后训练样例）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_rl/deepseek/verl_patches/scripts/internal/`](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_rl/deepseek/verl_patches/scripts/internal)（verl 训练启动子脚本：`recompute_old_log_prob`、`n_samples`、GBS 等 GRPO 配置项入口）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/models/loss/grpo_actor_loss_func.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/loss/grpo_actor_loss_func.py) / [`dapo_actor_loss_func.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/loss/dapo_actor_loss_func.py) / [`ppo_actor_loss_func.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/models/loss/ppo_actor_loss_func.py)（`_compute_*_policy_loss`：GRPO KL 进损失、DAPO 解耦 clip + token_level_loss + kl_loss≡0、PPO 对称 clip 无 KL；`old_log_prob=None → ratio≡1`）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/trainer/utils/compute_utils.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/trainer/utils/compute_utils.py)（`compute_group_norm_advantage_return` 组内 z-score 去 critic 优势；`compute_gae_advantage_return` PPO GAE；`apply_kl_penalty` 把 KL 折进 PPO reward）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`mindspeed_rl/trainer/grpo_trainer_hybrid.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/trainer/grpo_trainer_hybrid.py) / [`dapo_trainer_hybrid.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/trainer/dapo_trainer_hybrid.py) / [`ppo_trainer_hybrid.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/mindspeed_rl/trainer/ppo_trainer_hybrid.py)（`fit` 三阶段编排；`set_actor_log_prob_skip_flag` on-policy 免算；`dynamic_sampling` 过滤零梯度组 + 补采上限；PPO `CriticWorker`/`compute_values`/`update_critic`）
- [mindspeed-rl](https://gitcode.com/Ascend/MindSpeed-RL) — [`cli/train_dpo.py`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/cli/train_dpo.py)（DPO 委托 `mindspeed_llm.tasks.posttrain.dpo.DPOTrainer`，`is_pairwise_dataset` 成对偏好、纯 Megatron 训练、无 rollout）+ [`docs/zh/algorithms/{grpo,dapo,ppo,dpo}.md`](https://gitcode.com/Ascend/MindSpeed-RL/blob/398fd9a5fa6358c50071db2d09919e414accea90/docs/zh/algorithms/dapo.md)（DAPO `clip_ratio_low/high`、`token_level_loss`、`filter_groups_*`、`overlong_buffer_*` 默认值与各算法端到端 tps）

## Links

- [verl](../frameworks/verl.md)（GRPO 的承载框架：单控制器控制流 + 多控制器计算流，驱动 rollout/ref/update 三阶段）
- [deepseek-r1-rl](../../guides/recipes/deepseek_r1_rl.md)（GRPO 的端到端实践：671B / A3 128 卡 / 全共卡 / 123 TPS）
- [deepseek-r1](../../../inference/concepts/models/deepseek_r1.md)（跨域：本 RL 实践训练的目标模型，加载 DeepSeek-V3-671B 权重）
- [sam-speculative](sam_speculative.md)（SAM 投机加速 GRPO/DAPO 的 rollout 生成）
- [rollout-rebalance](rollout_rebalance.md)（rollout 均衡调度服务 on-policy 采样）
- [length-aware-resampler](length_aware_resampler.md)（长度感知重采样优化 rollout）
- [qwen2.5-rl](../../guides/recipes/qwen2_5_rl.md)（Qwen2.5 入门用 GRPO）
- [qwen3-rl](../../guides/recipes/qwen3_rl.md)（Qwen3 235B/32B 用 GRPO/DAPO 2k+32k 长序列）
- [scalebox](../frameworks/scalebox.md)（Code RL 沙盒(配 GRPO/DAPO 奖励)）
- [agent-rl-loop](agent_rl_loop.md)（agent RL 多轮工具调用执行范式）
- [qwen3-tool-agent-rl](../../guides/recipes/qwen3_tool_agent_rl.md)（Qwen3 tool agent RL）
- [qwen2-code-rl-scalebox](../../guides/recipes/qwen2_code_rl_scalebox.md)（ScaleBox Code RL）
- [mindspeed-rl](../frameworks/mindspeed_rl.md)（MindSpeed-RL 框架实现 GRPO/DAPO/PPO/DPO）
- [rule-reward-verifier](rule_reward_verifier.md)（GRPO/DAPO/PPO 的规则奖励打分器：数学题 boxed 答案匹配 ±1）
- [transferdock-data-scheduling](transferdock_data_scheduling.md)（GRPO/DAPO 一轮迭代的数据面：各 Ray worker 经 GRPOTransferDock 取放样本）
- [partial-rollout](partial_rollout.md)（长尾 rollout 暂停续跑，封顶单步 rollout 时长）
