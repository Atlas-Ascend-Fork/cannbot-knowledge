---
{
  "type": "Runbook",
  "title": "KL-Cov 策略损失移植 vime（torchtitan/megatron 双后端）与 --keep-old-actor 生效前提",
  "description": "把论文 arXiv:2505.22617 的 KL-Cov 惩罚（verl PR #1830 loss_mode=kl_cov）移植进 vime：ppo_utils 新增 compute_kl_cov_loss（无 clip 的 -A·ratio 主项 + top 协方差 token 上 β·|Δlogp| 惩罚），megatron/torchtitan 两后端接入，--use-kl-cov/--kl-cov-ratio/--kl-cov-coef 三参数与互斥校验，run/resume/replay 三脚本默认启用。关键前提是 --keep-old-actor：async 单步更新下 old log probs 用当前权重预计算会使 Δ≡0、惩罚恒为 0。实机 27 步验证 loss 管道与 TB 指标（kl_cov、pg_clipfrac）落盘。注意：协方差选择位置缺陷（修复与验证边界见正文）在该 27 步运行中尚未修复。",
  "tags": [
    "task.implementation",
    "topic.graph_execution",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# KL-Cov 策略损失移植 vime（torchtitan/megatron 双后端）与 --keep-old-actor 生效前提

## 适用场景

- 框架：vime（RL 训练框架，本例仓库 `${VIME_ROOT}`，分支 `codex/qwen35-36-normal-rl`），含 megatron 与 torchtitan 两个训练后端；本例实机走 torchtitan 后端 + vLLM rollout（async 流水线、`--update-weights-interval 1`、TIS 开启、每 rollout 一次 optimizer step）。
- 模型与负载：Qwen3.5-4B（VLM，`--freeze-params-name-list vision_encoder`），terminal-bench agentic RL（每步 8 prompt × 16 samples = 128 attempts、~2.6M token/步、32768 token/微批打包预算、LR 1e-6、temperature 1.0）。
- 硬件：华为 NPU，8 die = TP=4/DP=1 训练 + 4 个 TP=1 vLLM rollout 引擎（`--train-env-vars '{"TORCH_NPU_DEVICE_CAPABILITY":"8.0"}'`）。
- 目标：把论文《The Entropy Mechanism of Reinforcement Learning for Reasoning Language Models》（arXiv:2505.22617，Cui et al. 2025）的 KL-Cov 惩罚（verl 主库 PR #1830，`loss.mode=kl_cov`）移植进 vime，替换原"冻结 ref KL 锚"（`--use-kl-loss --kl-loss-coef 0.001 --ref-load`——论文 Fig.10 证明其稳熵但牺牲性能）。
- 缺失信息说明：本地开发机无 torch（`ModuleNotFoundError: No module named 'torch'`），loss 数值只能靠 py_compile/ruff/bash -n/dry-run 与纯 Python 副本验证，实机路径由训练机运行闭环。

路径约定：`${VIME_ROOT}` 为vime 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

相关机制：[KL-Cov 单 response 微批中心化退化与 step 级选择修复](cov_grpo_response_step.md)。下述 27 步运行发生在此修复前，不作为修复后的验证。

## 触发与观测

原 run 脚本用冻结初始 checkpoint 的 KL 锚防熵坍缩。用户要求引入 verl 社区已合入的 KL-Cov 替代。调研确认（事件 74/79/87/89）：KL_Cov/Clip_Cov 已通过 PR #1830 合入 verl main，入口是 `loss.mode`；PRIME-RL 官方 repo 提供 7B recipe 脚本（`recipe/dapo/7b_kl_cov.sh`，含论文验证过的超参）。

实机 27 步运行后（用户回贴的 TensorBoard 导出，事件 1090，单次观测）：loss 管道未崩溃，`kl_cov` 指标落盘且第 1 步=0、随后 4.07e-5→6.76e-5→…→峰值 8.3e-4 后回落至 1e-4~2.5e-4 震荡；`entropy_loss` 0.2525→0.0189。注意：该运行使用的是初版实现，其协方差选择位置有缺陷（见姊妹卡 [KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界](cov_grpo_response_step.md) 的修复），指标链路有效不等于选择正确。

## 探针与操作

核心移植（`vime/utils/ppo_utils.py` 新增 52 行，事件 154）：

```python
def compute_kl_cov_loss(
    log_probs: torch.Tensor,
    old_log_probs: torch.Tensor,
    advantages: torch.Tensor,
    loss_masks: torch.Tensor,
    kl_cov_ratio: float,
    kl_cov_coef: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """KL-Cov policy loss from "The Entropy Mechanism of Reinforcement Learning
    for Reasoning Language Models" (arXiv:2505.22617, Eq.10/13/14), ported from
    verl's ``loss_mode="kl_cov"`` (PR #1830).

    Replaces the PPO-clipped surrogate with the unclipped ratio loss
    ``-A * pi/pi_old`` and adds ``kl_cov_coef * |log pi - log pi_old|`` on the
    top-``kl_cov_ratio`` fraction of valid tokens ranked by the batch-level
    covariance ``(logp - mean(logp)) * (A - mean(A))`` — the high-covariance
    tokens that drive entropy collapse. The KL reference is the old policy
    (rollout / previous iterate), NOT a frozen reference model.

    All inputs are flat per-token tensors. Selection runs on detached tensors
    over the local (micro-batch / CP-shard) valid tokens, mirroring verl's
    per-mini-batch selection; the penalty keeps gradients through ``log_probs``.

    Returns:
        (pg_losses, selected, kl_cov_penalty): per-token unclipped pg loss with
        the penalty added; ``selected`` (1 on penalized tokens, reported in
        place of pg_clipfrac); ``kl_cov_penalty`` (the added ``coef*|delta|``
        term, for the "kl_cov" metric).
    """
    negative_approx_kl = log_probs - old_log_probs
    abs_kl = negative_approx_kl.abs()
    ratio = torch.exp(negative_approx_kl)
    pg_losses = -advantages * ratio

    selected = torch.zeros_like(pg_losses)
    valid = loss_masks > 0
    n_valid = int(valid.sum().item())
    if n_valid > 0:
        with torch.no_grad():
            valid_idx = torch.nonzero(valid, as_tuple=True)[0]
            valid_adv = advantages[valid]
            valid_logp = log_probs[valid].detach()
            covs = (valid_adv - valid_adv.mean()) * (valid_logp - valid_logp.mean())
            k = min(n_valid, max(1, int(n_valid * kl_cov_ratio)))
            top_local = torch.topk(covs, k).indices
            selected[valid_idx[top_local]] = 1.0

    kl_cov_penalty = kl_cov_coef * abs_kl * selected
    pg_losses = pg_losses + kl_cov_penalty
    return pg_losses, selected, kl_cov_penalty
```

两后端 `policy_loss_function` 接入（megatron loss.py:906 区、torchtitan loss.py:563 区，事件 161/171）：`pg_clipfrac` 复用为被惩罚 token 占比，新增 `kl_cov` metric。参数与互斥校验（`vime/utils/arguments.py`，事件 189/192）：

```python
    if args.use_kl_cov:
        assert args.loss_type == "policy_loss", "--use-kl-cov requires --loss-type policy_loss"
        assert not args.use_kl_loss, "--use-kl-cov and --use-kl-loss are mutually exclusive"
        assert args.kl_coef == 0, "--use-kl-cov is incompatible with reward-shaping KL (--kl-coef)"
        assert args.advantage_estimator != "gspo", "--use-kl-cov is incompatible with the gspo advantage estimator"
        assert not args.use_opsm, "--use-kl-cov is incompatible with --use-opsm"
        assert 0 < args.kl_cov_ratio <= 1.0, "--kl-cov-ratio must be in (0, 1]"
```

run/resume/replay 三脚本默认启用（最终态为环境变量可覆盖，事件 1230/1233）：

```bash
export TB_KL_COV_RATIO="${TB_KL_COV_RATIO:-2e-3}" TB_KL_COV_COEF="${TB_KL_COV_COEF:-1.0}"

    --use-kl-cov --kl-cov-ratio "$TB_KL_COV_RATIO" --kl-cov-coef "$TB_KL_COV_COEF" --keep-old-actor
```

超参取值依据（事件 1079/215）：ratio 论文锚点 7B→2e-3、32B→2e-4（模型越大协方差分布越重尾，论文 Table 1：top 0.02% token 协方差 5.654 vs 全体均值 0.003，差 2000 倍），4B 取最近锚点 2e-3；coef=1.0 为论文/verl/PRIME-RL recipe 三方一致；parser 默认值（2e-4）与脚本显式值分开。配套沿用 recipe：temperature=1.0、不开 entropy bonus / ref-KL、小 LR + grad clip 兜底稳定性（该模式下 `--eps-clip 0.2/0.32` 变为惰性参数）。

## 机制与判别

**结论 c1**：KL-Cov（arXiv:2505.22617，verl loss_mode=kl_cov / PR #1830 的移植）在 vime 中以 ppo_utils.py 新增 52 行的核心函数 compute_kl_cov_loss 落地：无 clip 的 -A·ratio 主项 + 对 top 协方差 token 施加 kl_cov_coef·|log π_θ − log π_old| 惩罚，按 verl 语义该模式下 PPO clip 整体移除，megatron 与 torchtitan 两后端 policy_loss_function 同步接入。证据：事件 154（实现）、161/171（两后端）、197/206（编译与 lint）；diff 统计（事件 276）：ppo_utils +52、两 loss 各 +20/+16、arguments +40 行。

**结论 c2**：vime async 单步更新下 old log probs 默认用当前权重预计算，Δ≡0、惩罚恒为 0；必须配 --keep-old-actor 让 old log probs 来自上一代 rollout 权重快照（torchtitan 后端 init 时 copy(actor)→old_actor、每次 weight push 后 rollout_actor→old_actor 轮转），首步 kl_cov=0 是设计使然而非故障。证据：torchtitan `actor.py` 既有实现（事件 229，147-154 行）：

```
147:         if getattr(args, "keep_old_actor", False):
148:             # Initialize old_actor = actor (PPO ratio=1 on the first update; semantically
149:             # correct since old_actor is the "previous policy" and actor starts from the
150:             # same seed weights). Using copy instead of load_other_checkpoint avoids the
151:             # DCP-format limitation of load_other_checkpoint (only HF safetensors supported).
152:             self.weights_backuper.copy(src_tag="actor", dst_tag="old_actor")
153:             if args.update_weights_interval == 1:
154:                 self.weights_backuper.backup("rollout_actor")
```

实机 TB 首行 kl_cov=0、第 2 步起非零（事件 1090）与该语义吻合。代价：多一份 CPU 权重快照（4B bf16 ≈ 8GB host）。replay 脚本注意（事件 256 注释）：debug_train_only 模式跳过 update_weights，轮转不执行，old_actor 停在初始权重——惩罚锚的是 replay 起点策略而非逐步策略。

**结论 c3**：实机 27 步（单次观测，Qwen3.5-4B、torchtitan、TP=4/DP=1、NPU、ratio=2e-3/coef=1.0/keep-old-actor）中该 loss 管道未崩溃且 TB 指标落盘：kl_cov 第 1 步=0、随后 4.1e-5→6.8e-5、峰值 8.3e-4 后回落至 1e-4~2.5e-4 震荡；注意该运行使用的是初版实现（协方差选择位置有误，见姊妹卡 [KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界](cov_grpo_response_step.md)），指标链路有效不等于选择正确。（数据来源：用户在训练机导出的 TensorBoard 三列数据——reward/kl_cov/entropy，事件 1090，非本会话内工具结果。）

**结论 c4**：TB 中 kl_cov 是摊到全部 token 的平均惩罚（被选中率稀释约 500 倍），换算选中 token 漂移需除以 pg_clipfrac（该模式下 pg_clipfrac 复用为被惩罚 token 占比，应恒 ≈ ratio）；这项派生值没有在本任务建立通用正常区间；增长或归零只能作为检查旧权重、数据和 mask 的线索，不能独立判定轮转或参考分布失效。换算公式 `kl_cov = β × 选中率 × E_selected[|Δlogp|]`（事件 877）；`analyze_train_util.py` 的 loss 组成段（解析 `train metrics @ rollout_id=N: {...}` 行，派生 `选中 token 平均惩罚 β·|Δ| = kl_cov/clipfrac`）已用合成日志端到端验证（事件 913/916：mean 0.024 / p50 0.030 nats 的派生计算正确）。

未验证推断：vime async 每批 1 次 optimizer step 的单步锚定比论文每 rollout 8 次 minibatch 更新的批内锚定弱，预期效果是"熵下降明显变缓"而非拉平（事件 1239）——待实机重启验证。

## 验证信号

- py_compile 四文件通过、ruff 零新增（7 个 B905 为 HEAD 既有，`git show HEAD` 复核确认，事件 197/206/208）。
- bash -n 三脚本通过（事件 261）；run --dry-run 组装出正确命令（含新 flag、无 --ref-load，事件 265）。
- commit 3f8ebf3a 推送成功、远端 hooks 通过（事件 298）；后续 6c32d0d3/db702947 两次增量提交均推送成功（事件 1187/1237）。
- 实机信号（单次观测、证据等级：用户回贴的 TB 导出，事件 1090）：kl_cov 曲线存在且形态符合 keep-old-actor 语义（首步 0、随后非零）；pg_clipfrac 报选中率。
- 无性能类结论：未做同口径 baseline 对比，不声明加速/精度收益。

## 适用与失效边界

- 生效前提：`--keep-old-actor`（async 单步更新下否则惩罚恒 0）；GRPO/整条共享 advantage 的估计器；`loss_type=policy_loss`。与 `--use-kl-loss`/`--kl-coef`/gspo/opsm 互斥（启动时断言拦截）。
- 该模式下 PPO clip 被整体移除（verl 语义），`--eps-clip*` 惰性；稳定性依赖小 LR + grad clip。
- 初版实现的选择粒度退化（GRPO 单 response 微批下协方差为零）在 6c32d0d3 中改为本 rank step 级选择；该调整只验证了索引分桶与静态链路，修订后的实机训练效果尚未验证——若在其它框架移植，需检查"选择粒度 vs advantage 粒度"是否匹配（详见姊妹卡 [KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界](cov_grpo_response_step.md)）。
- replay/debug 模式下 weight 轮转不执行，惩罚锚定语义退化为"replay 起点策略"。
- microbatch 局部 top-k 有 `max(1, int(N*ratio))` 保底：microbatch 有效 token 太少时 ratio 失真；有效选中率应按实际 k/n 报告；取整误差取决于 n×ratio，不能用固定 token 数保证精确。当前 step 级实现还需记录 CP 长度不匹配而排除的样本。
- 停止/回退条件：TB `kl_cov` 持续为 0 时，检查 old/new logprob、选中 mask、权重轮转及指标分母；首步为零本身可符合设计。熵或 reward 变化不足以单独决定 ratio/coef 的调整，需固定其他条件做训练对照。本轨迹没有验证调参处置规则。
