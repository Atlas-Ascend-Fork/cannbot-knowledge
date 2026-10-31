---
type: Concept
title: 规则奖励 / Verifier（数学·格式校验的无模型奖励）
description: MindSpeed-RL 的规则奖励以确定性 verifier 直接给 rollout 响应打分，不运行 reward model。RuleReward worker 从 TransferDock 读取响应与标签，按 verifier_function 分发数学正确性、格式和推理步骤校验，再用 verifier_weight 加权生成 rm_scores。数学路径支持数值/符号等价、Math-Verify、mathruler 与 DAPO strict-box/长度惩罚；子进程池和逐样本超时隔离异常。全共卡模式因此无需独立 reward_resource。
tags:
- task.optimization
- topic.reinforcement_learning
status: stable
sources:
- resource: cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/README.md
  role: primary
- resource: cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/mindspeed_rl/workers/rule_reward.py
  role: supporting
created_at: '2026-06-30T00:00:00Z'
updated_at: '2026-10-29T15:24:42Z'
platforms:
- agnostic
---

# 规则奖励 / Verifier（数学·格式校验的无模型奖励）

## Summary

RLVR（Reinforcement Learning with Verifiable Reward，可验证奖励 RL）把奖励信号交给**确定性的规则/验证器**而非一个训练出来的 reward model：对一条 rollout 响应，直接用「答案是否对、格式是否合规」算出标量奖励。MindSpeed-RL 的 `RuleReward` worker 就是这条路径的落地——它在 RL 流水的 reward 阶段从 TransferDock 取出 `prompts/responses/labels`，按配置的一组 verifier 逐响应打分、加权求和，再把 `rm_scores` 写回，供 advantage 估计（[grpo-dapo](grpo_dapo.md)）使用。核心机制三类：**数学答案校验**（抽取 `\boxed{}` 答案后与标准答案做数值/符号比对）、**DAPO 数学 reward**（二值正误 + soft overlong 长度惩罚）、**格式与推理结构校验**（`<think>/<answer>` 标签、步骤模式正则）。因为奖励来自规则而非模型前向，reward 阶段不占独立的 NPU 资源——规则路径由独立的 CPU `RuleReward` Ray actor 承担，trainer 通过 `compute_rm_score.remote()` 调用。`RewardWorkerBase` 则加载 reward 模型执行模型打分，两者不可混同；集成模式禁配 reward_resource 也不能证明规则打分在 Actor 内联。

> 各 verifier 的判分机制与奖励组合方式见下文各节。RuleReward worker 如何从队列消费/回写经验、保证消费顺序的 DP 切分，属于数据调度，见 [transferdock-data-scheduling](transferdock_data_scheduling.md)；奖励进入 advantage 后的策略更新见 [grpo-dapo](grpo_dapo.md)。

## 无 reward model 的规则奖励：RuleReward worker 在流水里的位置

`RuleReward` 是个 Ray actor（`workers/rule_reward.py`），消费阶段名为 `rule_reward`。它的 `compute_rm_score` 是一个「取一批→打分→回写」的循环，直到 TransferDock 该阶段的经验全部消费完：

- **取经验**：从 `cur_td.get_experience` 拉 `['prompts', 'responses', 'response_length', *dataset_additional_keys]`（`labels` 即标准答案就在 `dataset_additional_keys` 里），`get_n_samples=True` 一次取齐同一 prompt 的 `n_samples_per_prompt` 条响应；多轮工具场景额外带 `tool_call_num`。
- **类别掩码**：仅非多模态路径：若数据带 `categories` 列，只有 `categories[:,0]` 为真的样本走规则校验（混合数据集里非可验证样本被跳过），其余被滤掉；多模态分支不使用该掩码，直接逐条调用 math_compute_score。
- **打分**：调 `compute_verifier_score` 得到每条响应的标量分 `rm_scores`（形状对齐 `response_length`）。
- **回写**：`put_experience({"rm_scores": ...})`；同时把各 verifier 的逐样本指标 `*_rewards/mean` 累加进 metrics。

奖励完全由 CPU 上的规则计算得出，不跑任何模型前向——这是它能在全共卡部署里「不另占卡」的根因：MindSpeed-RL 的 `validate_rl_args` 在 `use_integrated_worker` 下显式**禁止**配置 `reward_resource`，该配置限制与规则 worker 的承载位置是两个问题；规则奖励由独立 RuleReward actor 执行，RewardWorkerBase 的模型前向属于模型奖励路径。

## verifier 分发表与加权组合

打分的核心是 `rule_verifier.py::verifier`：它把配置项 `rl_config.verifier_function`（一个名字列表，默认 `["base_acc"]`）映射到具体打分函数，对每条响应分别算分，再按 `rl_config.verifier_weight`（默认 `[1.0]`）加权累加成最终奖励：

```python
rewards = [0.0] * len(labels)
for idx, fun in enumerate(verifier_function):
    scores = rule_verifier_function[fun](sequences=responses, answers=labels, tool_call_nums=tool_call_nums)
    metrics[f'{fun}_rewards/mean'] = scores
    rewards = [r + s * verifier_weight[idx] for r, s in zip(rewards, scores)]
```

这样「答案正确性 + 格式合规 + 步骤完整」可以各配一个 verifier 与权重线性叠加。可用的分发键（`rule_verifier_function`）：

| verifier 键 | 判分内容 | 后端 |
|---|---|---|
| `acc` | 抽答案 + 数值/符号比对，带错答/缺 box 的负分梯度 | `math_eval_toolkit`（sympy） |
| `base_acc` | 严格格式门控 + 答案正确（默认 verifier） | `mathruler` |
| `math_17k_acc` | 仅答案正确（无格式门） | `mathruler` |
| `acc_for_ppo` | 仅答案正确（`\boxed` 抽取 + grade） | `mathruler` |
| `math_verify_reward` | 格式门控 + Math-Verify 库判等 | `math-verify` |
| `acc_for_dapo` | 二值正误（minerva / strict-box） | `math_dapo` |
| `retool_reward` | strict-box 二值 + 工具调用补偿 | `math_dapo` |
| `format` | `<think></think><answer></answer>` 正则 | 正则 |
| `strict_format` | 标签计数 + 先后次序结构校验 | 正则 |
| `step` | 分步推理标志计数（封顶 1.0） | 正则 |

不在表内的名字被静默跳过。下面按机制分组展开。

## 数学答案校验：抽取答案 + 数值/符号双路比对

`acc` verifier（`accuracy_reward`）是最细的数学判分。每条响应在子进程里跑 `acc_worker`：先把响应裁到 `<|im_start|>assistant` 之后、在 `</s>`/`<|im_end|>`/`<|endoftext|>` 处截断，再用 `extract_answer(pred_str, data_name="math")` 抽出答案串，与标准答案过 `math_equal`。打分是**带梯度的负分**而非纯 0/1：

- 抽到答案且 `math_equal` 判等 → **1.0**；
- 抽到答案但不等 → **−0.5**；
- 抽到答案但响应里根本没有 `boxed` → **−1.0**；
- 抽不到答案 → **−1.0**。

判等核心 `math_equal`（`math_eval_toolkit/grader.py`）走两条路，命中任一即算对：

- **数值相等**：双方都能转成数字时，用 `isclose(rel_tol=1e-4)` 比较，并把标准答案的 `[ref/100, ref, ref*100]` 三种百分比变体都试一遍（容忍「85」与「0.85」「85%」混写）。
- **符号相等**：把两边分别用 `parse_expr → parse_latex → latex2sympy` 逐个尝试解析成 sympy 表达式，命中下列任一即等——字符串相等、`a == b`、`a.equals(b)`、`simplify(a - b) == 0`、`N(a)` 与 `N(b)` 数值相近，或矩阵逐元素 round-3 相等。元组/区间/`pmatrix` 还会拆分递归比对每个分量。

这套比对让「分数 vs 小数」「不同 LaTeX 写法」「等价代数式」都能判对，是规则奖励能逼近人工判分的关键。

## 两套数学后端：math-verify 与 mathruler

除了上面的 sympy 工具箱，仓库还接了两套现成判等后端，对应不同 verifier：

- **mathruler**（`base_acc` / `math_17k_acc` / `acc_for_ppo`）：用 `extract_boxed_content` 取 `\boxed{}` 内容、`grade_answer` 判等。`base_acc`（默认 verifier）在判等之外加**严格格式门**——响应须匹配 `<think>…</think>…<answer>…\boxed{…}…</answer>`（DOTALL）才有分；`math_17k_acc`/`acc_for_ppo` 则只看答案对错，不要求标签。
- **Math-Verify 库**（`math_verify_reward`，`math_verify.py::compute_math_score`）：用 `math_metric` 配 `LatexExtractionConfig`（gold）与 `ExprExtractionConfig + LatexExtractionConfig`（pred），把标准答案包进 `\boxed{}` 后调库判等；同样先过 `<think>/<answer>/\boxed` 格式正则，不合规直接 0 分。

三套后端（sympy 工具箱 / mathruler / Math-Verify）解决的是同一件事——鲁棒地判断「学生答案 ≡ 标准答案」，区别在解析器与格式门的严苛程度，按数据集选用。

## DAPO 数学 reward：二值 strict-box/minerva + soft overlong 惩罚

`acc_for_dapo`（`math_dapo.py::compute_score`）是 DAPO 配套的数学奖励，特点是**纯二值**：正确 **+1.0**、错误 **−1.0**，没有中间的 −0.5 梯度。它先把响应裁到末尾 300 字符（MATH-500 最长答案 159 字符），再二选一校验：

- **minerva 模式**（默认）：用 `Answer:\s*(...)` 正则抽答案，两边都过 `normalize_final_answer`（剥单位词、规范 `\frac`/`\sqrt`/`\boxed` 简写、去千分位逗号）后字符串比较。
- **strict-box 模式**（`strict_box_verify=True`）：只看响应末尾 100 字符里的 `\boxed{}`，抽出内容与标准答案**严格相等**才给 1，否则 −1。

`retool_reward` 在 strict-box 基础上加**工具调用补偿**：多轮 RL 里若答案判负但模型确实调了工具，给 `tool_call_num * 0.1` 的补偿、并用 `min(0, score + bonus)` 封顶在 0——不奖励错误答案，但缓和「调了工具仍错」的惩罚，鼓励工具使用行为。

DAPO 的另一招 **soft overlong punishment**（软超长惩罚）不在 verifier 里，而在 `compute_verifier_score` 末尾按响应长度叠加：开 `overlong_buffer_enable` 后，设缓冲区 `overlong_buffer`、期望长度 `expected_len = rollout_max_tokens − overlong_buffer`，对超出 `expected_len` 的部分线性扣分

$$\text{overlong\_reward} = \min\!\Big(-\frac{\min(\text{len}-\text{expected\_len},\ \text{buffer})}{\text{buffer}}\times\text{penalty\_factor},\ 0\Big)$$

即进入缓冲区后惩罚随超长线性增长、到缓冲区尾封顶，超过期望长度才扣、未超不扣。这把「别写太长」做成按响应长度计算的分段线性奖励惩罚附加到答案奖励上；实现通过 response_length.item()、Python 列表再新建 tensor 计算，不保留长度到奖励的可反向图，策略通过奖励信号优化而非直接对长度求导。

## 格式与推理结构校验

不依赖标准答案的 verifier 校验响应的**形状**：

- `format`（`format_reward`）：用 re.match 与 DOTALL|MULTILINE 匹配 `^<think>.*?</think>\s*<answer>.*?</answer>$` → 1.0 否则 0.0；$ 可匹配行尾，标签后接换行及额外文本仍可能通过，不等同于 re.fullmatch 的整串校验。
- `strict_format`（`strict_format_reward` → `_validate_response_structure`）：更严——要求 `<think>`/`</think>`/`<answer>`/`</answer>` 各恰好出现一次、`\boxed{}` 恰好一处，且**先后次序**正确（think_start < think_end < answer_start，answer_start < boxed_start < answer_end），并须以 `<think>` 开头、`</answer>` 结尾；通过给 1.0、结构错给 −0.5。
- `step`（`reasoning_steps_reward`）：数 `Step N:`、`^N.` 编号、`-`/`*` 列表项、`First,/Second,/Next,/Finally,` 过渡词的出现次数，按 `min(1.0, count/3)` 给分——鼓励至少三段可见的分步推理，但不强制更多。

这些格式分通常以小权重叠加在答案正确性之上（`verifier_weight`），既塑形输出结构、又不喧宾夺主压过答案对错。

## 进程池隔离与逐样本超时

sympy/latex 解析与正则回溯遇到对抗样本可能挂死或炸内存，`acc`（sympy 判等）与 `strict_format`（结构校验）两个 verifier 不在主进程直接算，而是提交到一个全局单例 `GlobalProcessPool`（`ProcessPoolExecutor`，`max_workers=16`）的子进程，并对每条样本设 **1 秒超时**：超时或异常一律记 0 分而非让整个 reward 阶段卡住。进程池在 broken 时自动重建。mathruler 系的 `base_acc`/`math_17k_acc`/`acc_for_ppo`（`grade_answer`）与 DAPO/Math-Verify 系判等则直接在主进程内联算、不入池。这是规则奖励在大批量 rollout 下保持稳定吞吐的工程保障。

## reward 组合、归一化与 DAPO 过滤信号

`compute_verifier_score` 把 verifier 加权和叠加 overlong 惩罚后，reshape 成 `response_length` 的形状作为 `rm_scores` 回写。两处与 DAPO 协同：

- **DAPO 过滤指标**：开 `filter_groups_enable` 时，额外把 `metrics[filter_groups_metric]`（默认 `acc`）reshape 后作为 `metric_for_dapo` 一并回写，供 DAPO 动态采样按组内准确率过滤掉「全对/全错」的指标无方差样本组；最终奖励还可能因长度惩罚等不同，不保证优势为零（机制见 [grpo-dapo](grpo_dapo.md)）。
- **多模态分支的组内归一化**：多模态路径用 `math_compute_score`（acc 0.9 + format 0.1 加权）逐条打分后，把奖励按 `n_samples_per_prompt` 分组做 `(r − mean) / (std + 1e-6)` 标准化再回写 `token_level_rewards`——这一步本质就是 GRPO 的组内相对优势，在 reward 阶段就地完成。

至此，规则奖励把「数学对错 + 格式 + 长度 + 过滤信号」压成一份可被 advantage 直接消费的标量，全程零模型前向。

## Evidence

- [README.md](../../../../../cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/README.md)（primary）
- [rule_reward.py](../../../../../cann-recipes-raw/mindspeed-rl/adb494ad777ef4314bca717b56983feb67a41ea4/mindspeed_rl/workers/rule_reward.py)（supporting）

## Links

- [grpo-dapo](grpo_dapo.md)（规则奖励的下游：`rm_scores` 进组内相对 advantage；`metric_for_dapo` 服务 DAPO 动态样本过滤；overlong 惩罚是 DAPO 长序列约束）
- [transferdock-data-scheduling](transferdock_data_scheduling.md)（RuleReward worker 经 TransferDock 消费/回写经验，`guarantee_order` 的 DP 切分顺序）
- [mindspeed-rl](../frameworks/mindspeed_rl.md)（承载框架：规则由 CPU RuleReward Ray actor 打分；RewardWorkerBase 运行 reward 模型；集成模式禁配 reward_resource 是另一个配置约束）
