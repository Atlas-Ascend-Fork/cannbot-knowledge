---
{
  "type": "Runbook",
  "title": "KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界",
  "description": "GRPO 单 response 微批中 advantage 为常数时，中心化协方差失去区分 token 的信号，不能依赖 torch.topk 的并列索引顺序。轨迹实现 actor 侧 step 级选择 mask，并验证纯 Python 分桶回填与静态编译；尚未验证修订后的实机训练效果。27 步熵下降是故障观测，不能证明唯一根因或据此决定丢弃 checkpoint、调整 ratio。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [
    {
      "resource": "https://docs.pytorch.org/docs/2.9/generated/torch.topk.html",
      "role": "constraint"
    }
  ],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界

## 适用场景

- 框架/平台：vime RL 训练框架（torchtitan 与 megatron 双后端），Qwen3.5-4B terminal-bench agentic RL（每步 128 attempts、~2.6M token、GRPO advantage 整条 response 共享），NPU、32768 token/微批打包预算、async 每 rollout 一次 optimizer step。
- 触发条件类别：在微批内计算协方差，而该微批有效 token 的 advantage 全相同时，中心化在数学上为零；两条 response 若 advantage 不同则不一定出现此退化。实际浮点结果还需在目标后端检查。
- 参照实现：verl PR #1830 `loss.mode=kl_cov`（其 mini-batch 汇聚 256 条 response，中心化有意义）；论文 arXiv:2505.22617 Eq.10（中心化跨整个 batch 的 N 个 rollout token）。
- 缺失信息说明：本地无 torch，修复的数值验证只能用纯 Python 副本 + 暴力参考实现；实机重启验证发生在本轨迹之后（未闭合）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

**故障**：KL-Cov 已启用（`--use-kl-cov --kl-cov-ratio 2e-3 --kl-cov-coef 1.0 --keep-old-actor`）并实机运行 27 步，用户对比此前的 ref-KL 训练结果："感觉熵崩的问题根本就没有任何改善啊"（事件 1095）。TensorBoard 导出（事件 1090，用户回贴、单次观测）：

- `entropy_loss`：0.2525 → 0.0189（27 步，约 -92.5%；这是聚合指标下降，不能由 e 的均值指数推断每个位置的有效选择数或探索归零）；
- `kl_cov`：第 1 步 0，随后 4.07e-5→6.76e-5→…→峰值 8.3e-4（step 9）→回落 1e-4~2.5e-4 震荡——**指标活着**；
- `reward`：0.31→顶部 0.66（step 9-10，此时熵 0.07）→0.35-0.65 震荡无趋势。

该次 run 中惩罚指标有非零值，熵仍显著下降。用户比较的是此前 ref-KL run；轨迹没有同条件、无保护的对照，不能表述为“与不加保护无差别”。

## 探针与操作

**定位推理**（事件 1098）：初版在 microbatch 内选择，而单 response 的 GRPO advantage 整条共享，中心化协方差在数学上为零。建议在目标后端构造该微批，检查 `(adv - adv.mean())` 和 covs 的实际数值、记录 top-k 索引及重复调用结果；不要把“返回前 k 个位置”作为预期条件。PyTorch 的 [torch.topk 契约](https://docs.pytorch.org/docs/2.9/generated/torch.topk.html)不保证并列索引稳定，原 Agent 关于固定选择 response 开头的推断没有设备实验支持。

**修复（before → after）**：

before（初版，事件 154，per-microbatch 选择）：

```python
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
```

after（事件 1129，抽出 mask 施加函数 + step 级全局选择器）：

```python
def compute_kl_cov_penalty(
    log_probs: torch.Tensor,
    old_log_probs: torch.Tensor,
    advantages: torch.Tensor,
    selected_mask: torch.Tensor,
    kl_cov_coef: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """KL-Cov loss given a precomputed 0/1 selected mask (shared by the
    step-global selection path and the per-microbatch fallback).

    Returns (pg_losses, selected, kl_cov_penalty): unclipped ``-A*ratio`` plus
    ``kl_cov_coef * |log pi - log pi_old|`` on masked tokens; ``selected`` and
    ``kl_cov_penalty`` are for the pg_clipfrac / kl_cov metrics.
    """
    negative_approx_kl = log_probs - old_log_probs
    abs_kl = negative_approx_kl.abs()
    ratio = torch.exp(negative_approx_kl)
    pg_losses = -advantages * ratio
    kl_cov_penalty = kl_cov_coef * abs_kl * selected_mask
    pg_losses = pg_losses + kl_cov_penalty
    return pg_losses, selected_mask, kl_cov_penalty
```

```python
def compute_kl_cov_selection(
    log_probs: list[torch.Tensor],
    advantages: list[torch.Tensor],
    loss_masks: list[torch.Tensor],
    kl_cov_ratio: float,
) -> list[torch.Tensor]:
    """Step-global KL-Cov token selection — paper Eq.10 centering over the
    WHOLE batch's rollout tokens, computed once per training step in the actor
    (which sees every sample; the loss only sees one micro-batch at a time).

    Ranks tokens by ``(logp - mean) * (A - mean)`` over all valid tokens of the
    step and marks the top ``kl_cov_ratio`` fraction. Uses the pre-pass
    log_probs — under ``--keep-old-actor`` these are the old/rollout policy's,
    i.e. the same reference the penalty measures drift against.

    Returns per-sample 0/1 float masks aligned with (and on the device of)
    ``loss_masks``. Samples whose log_probs/advantages length mismatches the
    loss_mask (CP-sharded shards) are excluded from selection.
    """
    import bisect

    masks = [torch.zeros_like(m, dtype=torch.float32) for m in loss_masks]
    if not log_probs or log_probs[0] is None or not advantages:
        return masks
    device = advantages[0].device
    valid_slices: list[tuple[int, torch.Tensor]] = []  # (sample i, valid positions)
    adv_parts: list[torch.Tensor] = []
    logp_parts: list[torch.Tensor] = []
    for i, (lp, adv, m) in enumerate(zip(log_probs, advantages, loss_masks, strict=False)):
        if lp is None or adv is None:
            continue
        if lp.numel() != m.numel() or adv.numel() != m.numel():
            continue
        sel = m > 0
        if bool(sel.any()):
            valid_slices.append((i, sel.nonzero(as_tuple=True)[0]))
            adv_parts.append(adv[sel].to(device=device, dtype=torch.float32))
            logp_parts.append(lp[sel].detach().to(device=device, dtype=torch.float32))
    if not valid_slices:
        return masks

    adv_all = torch.cat(adv_parts)
    logp_all = torch.cat(logp_parts)
    covs = (adv_all - adv_all.mean()) * (logp_all - logp_all.mean())
    n = int(covs.numel())
    k = min(n, max(1, int(n * kl_cov_ratio)))
    top_positions = torch.topk(covs, k).indices.tolist()

    starts: list[int] = []
    total = 0
    for _, idxs in valid_slices:
        starts.append(total)
        total += int(idxs.numel())
    tops_by_sample: dict[int, list[int]] = {}
    for p in top_positions:
        s = bisect.bisect_right(starts, p) - 1
        i, idxs = valid_slices[s]
        tops_by_sample.setdefault(i, []).append(int(idxs[p - starts[s]]))
    for i, positions in tops_by_sample.items():
        masks[i][torch.tensor(positions, device=masks[i].device, dtype=torch.long)] = 1.0
    return masks
```

actor 侧注入点（torchtitan `actor.py`，`compute_advantages_and_returns` 之后；megatron 同构，事件 1277 为最终文件状态）。下列仅摘录执行语句，省略原注释中未经验证的并列索引顺序解释：

```
                if getattr(self.args, "use_kl_cov", False) and rollout_data.get("log_probs"):
                    from vime.utils.ppo_utils import compute_kl_cov_selection

                    rollout_data["kl_cov_selected"] = compute_kl_cov_selection(
                        rollout_data["log_probs"],
                        rollout_data["advantages"],
                        rollout_data["loss_masks"],
                        self.args.kl_cov_ratio,
                    )
                    n_sel = int(sum(int(m.sum().item()) for m in rollout_data["kl_cov_selected"]))
                    n_tok = int(sum(int(m.numel()) for m in rollout_data["kl_cov_selected"]))
                    logger.info(
                        f"kl_cov step-global selection: {n_sel}/{n_tok} tokens "
                        f"(ratio={self.args.kl_cov_ratio})"
                    )
```

loss 侧消费（torchtitan `loss.py`，事件 1277）：

```
    kl_cov_penalty = None
    if getattr(args, "use_kl_cov", False):
        # KL-Cov (arXiv:2505.22617 / verl loss_mode="kl_cov"): unclipped ratio
        # loss + abs-KL penalty toward the old policy on top-covariance tokens.
        # clipfrac reports the penalized-token fraction instead.
        kl_cov_selected = batch.get("kl_cov_selected")
        if kl_cov_selected is not None:
            # Step-global selection (actor precomputed): paper Eq.10 batch centering;
            # per-microbatch centering degenerates on 1-2-response microbatches.
            pg, clipfrac, kl_cov_penalty = compute_kl_cov_penalty(
                new, old, adv, torch.cat(kl_cov_selected).to(new.device), args.kl_cov_coef
            )
        else:
            pg, clipfrac, kl_cov_penalty = compute_kl_cov_loss(
                new, old, adv, torch.cat(loss_masks).to(new.device), args.kl_cov_ratio, args.kl_cov_coef
            )
    else:
        pg, clipfrac = compute_policy_loss(
            ppo_kl, adv, args.eps_clip, getattr(args, "eps_clip_high", args.eps_clip))
```

## 机制与判别

**退化条件**：GRPO 的 advantage 整条 response 共享一个值。若微批内所有有效 advantage 相同，中心化协方差在数学上均为零，无法据此区分 token；这不决定 top-k 的并列索引顺序。汇聚多条 advantage 不同的 response 可避免这一特定退化，但不保证选择一定有效；即使提升到 step 级，若所有有效 advantage 仍相同，信号依然退化。

**外部观测与因果边界**：27 步内熵从 0.2525 降至 0.0189，kl_cov 在第 1 步为零、此后出现非零值。该指标不能证明选择位置正确，也不能单独排除覆盖比例、训练配置等其他因素。选择粒度退化是需要核对的实现缺陷；修订后缺少同条件训练对照，不能认定它已经被证明为熵下降的唯一根因。[rollout dump 的 surprisal 分桶](../validations/rollout_dump_vllm_surprisal.md)也不能证伪“结构性”解释或证明语义决策预算。

**轨迹中的实现**：actor 在 compute_advantages_and_returns 后，对本 rank 全步 batch 的有效 token 按 (logp−mean)·(A−mean) 排名，生成 kl_cov_selected 0/1 mask 注入 rollout_data；loss 优先消费，缺失时回退原微批路径。新 key 同时加入两后端 get_batch 默认 keys 与 log_rollout_data 聚合跳过名单。DataIterator 为惰性读取，静态链路检查支持在消费前注入（事件 1104/1106/1115、1249–1286）。选择使用 pre-pass log_probs；ratio=2e-3、约 2.6M token 时选中量约 5200，但不同微批分别取整和 step 级取整未必精确相等。该实现改变了排名作用域，是否改善实际训练仍待验证；DP>1 的限制见下文。

**结论 c4（验证方法）**：修复的分桶回填逻辑（bisect starts/local index 映射）用纯 Python 副本对暴力参考实现验证：4 组 ratio + k=1 边界 + 长度不匹配样本跳过全部与参考一致——这是无 torch 环境可行的数值验证路径；实机重启后的生效判据是 train.log 每步出现 'kl_cov step-global selection: N/M tokens' 且 TB pg_clipfrac 稳定 ≈ ratio。

## 验证信号

- 事件 1183（工具结果）：`BUCKETING_OK: 4 组 ratio + k=1 边界 + 不匹配样本跳过 全部与暴力参考一致`——分桶索引（最易错部分）与暴力参考实现完全一致（纯 Python 副本，无 torch）。
- 事件 1176（工具结果）：`kl_cov_selected` 在 8 个文件中出现次数符合预期（ppo_utils 1、两 actor 各 3、两 loss 各 3、megatron model 1、torchtitan data 2、megatron data 1）；7 文件 py_compile 通过（COMPILE_OK）。
- 事件 1281/1284（工具结果）：最终全链路编译通过；8 个 lint 错误（MoE F401 + 7 个 B905）全部为 HEAD 既有，改动零新增（`git show HEAD` 对照确认）。
- 事件 1187（工具结果）：commit 6c32d0d3 推送成功、远端 hooks 通过。
- 实机重启后的冒烟判据（本轨迹内未执行，为建议命令，事件 1286）：

```bash
TB_REPLAY_FROM=${LOCAL_PATH_1} TB_REPLAY_STEPS=2 \
TB_ROLLOUT_BATCH_SIZE=2 TB_N_SAMPLES_PER_PROMPT=2 \
TB_TRAIN_TP=4 TB_TRAIN_DP=1 \
OUTPUT_DIR=${LOCAL_PATH_2} RUN_NAME=klcov-smoke VIME_SLOT=32 \
bash examples/terminal_agent_rl/replay-qwen35-4B-tbench-torchtitan.sh

# 三条信号（全过才算链路通）：
LOG=$(find ${LOCAL_PATH_2} -name train.log)
grep "kl_cov step-global selection" "$LOG"       # ① 每步一行 "N/M tokens"——全局选择在跑
grep -o "'train/kl_cov': [0-9.e-]*" "$LOG"       # ② 第1步=0、第2步>0——惩罚有值
grep -o "'train/pg_clipfrac': [0-9.e-]*" "$LOG"  # ③ ≈0.002——选中率正确（replay 用 2e-3）
```

- 证据等级说明：故障数据（27 步 TB 导出）为用户回贴（事件 1090），非本会话内工具结果；修复的实机效果（熵斜率是否变缓）未在本轨迹内验证——重启发生在轨迹结束之后。

## 适用与失效边界

- 适用：检查 GRPO/整条共享 advantage 的 KL-Cov 实现时，确认中心化作用域中确有 advantage 变化。step 级选择是本轨迹采用的办法，不存在由这些证据建立的通用最小 response 数量。
- 失效/退化条件：`rollout_data["log_probs"]` 缺失（如跳过 pre-pass）时守卫跳过，loss 自动回退 microbatch 路径——回退路径在单 response 微批下重新退化，需盯日志确认 `kl_cov step-global selection` 每步出现；CP 分片样本（长度不匹配）被排除在全局选择之外。
- 选择的作用域是本 DP rank 拿到的 rollout_data（actor 收到的是按 DP 切片后的数据）：中心化与 topk 覆盖"该 rank 的全步 batch"而非跨 DP 严格全局口径——DP=1 时两者重合（本例 TP=4/DP=1，故等价于全步 ~2.6M token 一次排序）；DP>1 时跨 rank 的严格全局排序需在聚合后的数据侧做，本实现未做，其与论文 Eq.10 口径的偏差未验证（属假设：若开 `--normalize-advantages`，advantages 已跨 DP whiten，中心化近似全局）。
- 旧 run 可作为故障记录，但不能替代修订后同条件对照。验证实现变化时先固定 ratio、coef、起始权重、采样和数据口径，避免同时调参后把收益归因于选择作用域。
- 是否恢复 checkpoint 或全新重启需单独对照。H=0.019 或桶占比显示 0% 都不能证明探索预算已耗尽；轨迹中的 ratio 调整、固定熵阈值和强制全新重启建议未获实机验证，本卡不作为处置规则推荐。
