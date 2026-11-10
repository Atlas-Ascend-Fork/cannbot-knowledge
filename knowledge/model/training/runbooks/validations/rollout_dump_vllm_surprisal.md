---
{
  "type": "Runbook",
  "title": "rollout dump 的采样 token surprisal 分桶：均值下降、百分比舍入与判读边界",
  "description": "用 vLLM rollout_log_probs 统计采样 token 的 surprisal 均值、分位数及各数值区间贡献。单次观测中均值从 0.2094 降至 0.0160 nats/token；后期两个高 surprisal 桶的 token 占比虽均显示 0%，仍分别贡献 29% 和 24% 的总 surprisal，不能判为归零。分桶不识别语法或决策位置，也不能单独裁决 KL-Cov 效果、探索预算或是否重启。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-04T02:06:31Z",
  "platforms": [
    "agnostic"
  ]
}
---

# rollout dump 的采样 token surprisal 分桶：均值下降、百分比舍入与判读边界

## 适用场景

- 框架/平台：vime RL 训练框架 + vLLM rollout（TIS 开启即记录 rollout_log_probs）、`--save-debug-rollout-data` dump（TB_DUMP_MODE=rollout、TB_SAVE_INTERVAL=6）；本例 Qwen3.5-4B terminal-bench agentic 负载、NPU、torchtitan TP=4/DP=1。
- 触发条件类别：RL 训练中 entropy_loss 持续下降，需要从生成侧 dump 补充采样 token 的 surprisal 分布，检查均值、分位数及少量大值的贡献。
- 工具无 torch 依赖（zip+pickle fallback 读 dump），可在任意机器运行。
- 缺失信息说明：未核对采样分布与所记录 logprob 的分布是否一致；dump 与 TB 的约 15%～20% 数值差未逐一分解；没有逐位置全分布熵或语义标注，不能据此识别“决策点”。

## 触发与观测

**触发**：KL-Cov 开着、实机 27 步熵 0.2525→0.0189（TB 导出，用户回贴、事件 1090）；用户进一步质疑（事件 1241）："你现在这个计算只是把熵算了吧，之前 TensorBoard 里的数据不是已经有了结果吗……能否作为最终裁决的工具呢"——即 TB 均值熵与 dump 分解到底差在哪、谁是裁决工具。

**观测**（实机 dump，事件 1223/1240，单次观测）。下列保留原脚本的标签和整数百分比；“纯结构”“决策”和“熵贡献”是历史输出名称，不代表已经验证这些语义：

```
== 0.pt: 457 samples (0 skipped), 2,294,116 response tokens ==
  rollout 熵估计 H = 0.2094 nats/token   surprisal p10/p50/p90/p99 = 0.00/0.00/0.65/3.19
  token 占比: <0.1 81%   <0.5 88%   >=1.0 7%
  per-sample H: p10 0.107  p50 0.222  p90 0.500
  桶                             token占比      熵贡献
  <0.1 nat  纯结构（语法/复制路径）             81%       2%
  0.1-0.5   半结构（高频命令壳）                8%      10%
  0.5-1.0   混合                        4%      15%
  1.0-2.0   决策（真选择点）                  4%      28%
  >=2.0     强决策（分叉/探索）                3%      45%

== 26.pt: 364 samples (2 skipped), 1,619,457 response tokens ==
  rollout 熵估计 H = 0.0160 nats/token   surprisal p10/p50/p90/p99 = -0.00/0.00/0.00/0.47
  token 占比: <0.1 98%   <0.5 99%   >=1.0 0%
  per-sample H: p10 0.009  p50 0.018  p90 0.070
  桶                             token占比      熵贡献
  <0.1 nat  纯结构（语法/复制路径）             98%       5%
  0.1-0.5   半结构（高频命令壳）                1%      20%
  0.5-1.0   混合                        0%      22%
  1.0-2.0   决策（真选择点）                  0%      29%
  >=2.0     强决策（分叉/探索）                0%      24%

== 熵轨迹（按传入顺序）==
  0.pt                     H=0.2094  决策token(>=1nat)占比 7%
  26.pt                    H=0.0160  决策token(>=1nat)占比 0%
```

后期 `>=1.0 nat` 两桶合计仍贡献约 53% 的总 surprisal。事件 1195 中的输出格式为 `.0%`，显示 `0%` 可以是小于约 0.5% 的正比例。原始输出没有精确计数，不能恢复准确占比，更不能把显示值当作空桶；上述 53% 也只是后期较低总量中的相对贡献。

## 探针与操作

探针命令（逐字，事件 1223）：

```bash
python3 tmp/scripts/analyze_dump_entropy.py $VIME_WORKSPACE/rollout_dumps/0.pt $VIME_WORKSPACE/rollout_dumps/26.pt
```

核心计算（tmp/scripts/analyze_dump_entropy.py，事件 1195；torch 缺失时 zip+pickle 直接读 data.pkl，与 replay 批次守卫同款 fallback）：

```python
        mask = s.get("loss_mask")
        if mask is not None and len(mask) == len(lp):
            vals = [-p for p, m in zip(lp, mask, strict=True) if m > 0]
        else:
            vals = [-p for p in lp]
        vals = [min(v, 20.0) for v in vals if v >= 0.0]  # clamp; drop numerics
        if not vals:
            skipped += 1
            continue
        surprisals.extend(vals)
        per_sample_h.append(sum(vals) / len(vals))
```

原脚本分桶定义（事件 1195，原文；区间可用于数值统计，括号内语义标签未经验证）：

```python
    buckets = (
        ("<0.1 nat  纯结构（语法/复制路径）", 0.0, 0.1),
        ("0.1-0.5   半结构（高频命令壳）", 0.1, 0.5),
        ("0.5-1.0   混合", 0.5, 1.0),
        ("1.0-2.0   决策（真选择点）", 1.0, 2.0),
        (">=2.0     强决策（分叉/探索）", 2.0, float("inf")),
    )
    total_h = sum(surprisals) / n
```

判读时只将各桶称为对应 surprisal 数值区间。token 占比是落在该区间的采样数占比；原脚本“熵贡献”列实际是该桶 surprisal 之和占全部保留样本 surprisal 之和的比例。比较多次 dump 时同时看均值、分位数、样本量、mask、跳过数量和各桶贡献。

建议补充精确的 `bucket_count/total_count`、未舍入比例和桶内 surprisal 总和；仅在 `bucket_count == 0` 时判为空桶。此输出改进未在原轨迹内执行，不能补造本例的精确计数。

## 机制与判别

**统计量与熵的条件**：在给定上下文下，只有 token 按分布 p 采样、记录的 logprob 也来自同一个 p，且没有截断或选择性丢弃时，才有 E[-log p(a)] = H(p)。若实际采样来自 q、记录的却是 p，期望为交叉熵 E_q[-log p(a)]。本例还将大于 20 nats 的值截断并丢弃部分值，实际输出应称为“清洗后采样 token 的平均 surprisal”，不能无条件宣称无偏策略熵。它提供生成侧的另一路观测，但也依赖 logprob、mask 和数据加载的正确性。

**判别能力的限制**：单个采样 token 的 surprisal 不等于该位置的全分布熵，也不直接表示语法或决策语义。例如所有位置都服从相同的二元分布 (0.99, 0.01)，每个位置的熵均约为 0.0560 nats；少见 token 的 surprisal 约为 4.605，占采样约 1%，却贡献约 82.2% 的期望 surprisal。这种集中不表示只有 1% 的位置具有不确定性。该反例为审查时的数学复核，不是本例的新训练实验。要分析位置不确定性或语义决策，需要相应的逐上下文分布或重复采样、语义标注等额外证据。

**本例支持的读数**：均值从 0.2094 降至 0.0160 nats/token，p99 从 3.19 降至 0.47。起点 `>=1 nat` 的采样 token 占比约 7%、贡献约 73%；后期其占比仅能确认显示为舍入的 0%，贡献仍约 53%。这些用户回贴的单次输出支持平均 surprisal 明显下降；不能证明剩余探索预算为零、每条轨迹有约 1400 个语义决策点，或 KL-Cov 无效完全由某个实现缺陷造成。

**与训练指标的对照**：dump 均值和 TB entropy_loss 均下降（起点 0.2094/0.2525，后期 0.0160/0.0189），但不是同一统计量的逐项一致性验证。bf16 记录、fan-out 的 loss_mask、生成与训练时的权重差异属于待核对因素，轨迹没有量化它们各自的影响；同向趋势不能证明两个通道都无 bug，也不能保证分桶相对占比不受口径影响。

KL-Cov 的协方差选择粒度应单独检查，见 [KL-Cov 单 response 微批中心化退化](../runtime/cov_grpo_response_step.md)；这份 dump 分桶不能代替该实现的运行验证。

## 验证信号

- 事件 1199（工具结果）：合成数值混合用例中，约 70% 的 surprisal 为 0.03、20% 为 0.3、10% 为 1.8，输出均值 0.2608、高值桶贡献约 69%；第二份 dump 也成功输出。该测试验证加载、聚合和分桶计算，不验证桶的语义标签或训练策略有效性。
- 事件 1203（工具结果）：py_compile + ruff All checks passed。
- 事件 1219（工具结果）：commit e379a0dd 推送成功。
- 实机观测（证据等级：用户回贴，事件 1223/1240；单次观测）：dump 均值和 TB 指标同向下降；后期高值两桶仍贡献约 29% 和 24%，整数显示不能作为空桶证据。
- 原轨迹曾提出全新重启和调整 ratio 的建议（事件 1239），但没有完成对应效果验证；本卡不将其采纳为由该统计量推出的处置规则。
- 无性能改善结论，也未在本次修订中重跑训练或重新读取实机 dump。

## 适用与失效边界

- 前提：dump 里存在 rollout_log_probs——仅在 TIS/记录 logprobs 开启时存在；缺失时脚本打印 `[skip] ...: no rollout_log_probs` 并跳过该 dump。
- 先核对采样策略、logprob 的分布定义、权重版本、token/mask 对齐和清洗规则；缺失条件时只报告实际统计量。
- 代码会把正无穷也截为 20，并丢弃负值和 NaN；原始日志没有提供各类清洗数量，不能假设其占比极小。mask 长度不匹配时会统计全部 lp，应单独报告，不能默认和正常样本可比。
- 桶阈值仅作数值切分。百分比须和精确计数、绝对总量一起解读；若只有整数显示，不能判定桶内样本为零。
- 没有逐位置分布和语义证据时，不判断“结构性/决策性熵”或探索预算。是否继续、重启或调整 KL-Cov 需结合受控训练对照、任务收益与实现验证，不能由本卡的桶占比阈值直接决定。
