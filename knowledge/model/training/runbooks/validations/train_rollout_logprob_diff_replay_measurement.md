---
{
  "type": "Runbook",
  "title": "train/rollout logprob 差异回放测量链路：纯 .pt 回放机制确认与 --train-logprobs-only 干跑接线验证",
  "description": "为定位 qwen3.5-9B 训练与推理 logprob 差异最大的环节，确认既有 replay-qwen35-9B-tbench-torchtitan.sh 为纯 .pt 回放（--load-debug-rollout-data 强制 debug_train_only，不启动 vLLM 引擎/沙箱/AgentENV，样本内 rollout_log_probs 为原始 run 落盘值），且训练侧已有 train_rollout_logprob_abs_diff 指标（CI 阈值 ≤0.1）。",
  "tags": [
    "task.testing",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# train/rollout logprob 差异回放测量链路：纯 .pt 回放机制确认与 --train-logprobs-only 干跑接线验证


## 适用场景

为定位 qwen3.5-9B 训练与推理 logprob 差异最大的环节，确认既有 replay-qwen35-9B-tbench-torchtitan.sh 为纯 .pt 回放（--load-debug-rollout-data 强制 debug_train_only，不启动 vLLM 引擎/沙箱/AgentENV，样本内 rollout_log_probs 为原始 run 落盘值），且训练侧已有 train_rollout_logprob_abs_diff 指标（CI 阈值 ≤0.1）。以 TB_LOGPROBS_ONLY=on --dry-run 验证接线：--train-logprobs-only 出现 3 次、--load-debug-rollout-data 正确指向回放目录，默认模式不受影响。所示机制片段为 rescore_replay.py 重算 fresh logprob 时与 recorded 逐元素 abs/signed diff 的代码段；quantile 替换与测量模式描述未进入账本证据。验证层级为静态/干跑检查，完整回放运行未在轨迹内展示。

## 触发与观测

触发：用户问题（是否存在/可否构造 train vs rollout log_absdiff 回放测量）。探针：grep log_absdiff/absdiff 全仓、读 replay 脚本与 --load-debug-rollout-data 参数链、读 train_rollout_logprob_abs_diff 计算与 CI 断言、读 rescore_replay.py/metrics_tis.py。观测：replay 为纯 .pt 回放；--train-logprobs-only 干跑接线正确且默认模式不变。

## 探针与操作

关键探针与修复操作。证据角色覆盖：implementation, validation。

## 机制与判别


> 回放机制确认：replay-qwen35-9B-tbench-torchtitan.sh 传 --load-debug-rollout-data 指向 dump 目录，该参数强制 debug_train_only（vime/utils/arguments.py:1781 'will not instantiate vLLM servers and will only run the training process'），RolloutManager 短路生成——rollout_id N 直接 torch.load 原始 run 用 --save-debug-rollout-data 存的 rollout_dumps/N.pt（vime/ray/rollout.py:654-658），回放不调 AgentENV/sandbox/verifier；训练侧既有 train_rollout_logprob_abs_diff 指标（megatron/torchtitan 两后端 loss.py 计算 (old-log_probs).abs()，CI 在 rollout_id=0 断言 ≤0.1）。


> 接线验证（干跑）：TB_LOGPROBS_ONLY=on bash replay-qwen35-9B-tbench-torchtitan.sh --dry-run 的 bash -x 轨迹中 --train-logprobs-only 出现 3 次、--load-debug-rollout-data 正确指向 $TB_REPLAY_LOAD_PATH 与回放目录；默认模式（不带 TB_LOGPROBS_ONLY）--train-logprobs-only 0 次、--keep-old-actor 与 --use-kl-cov 各 3 次保持不变——logprobs-only 开关只增不改默认训练路径。


```
        recorded = sample.rollout_log_probs
        if recorded is not None and len(recorded) == len(fresh):
            abs_diffs.extend(abs(f - r) for f, r in zip(fresh, recorded, strict=True))
            signed_diffs.extend(f - r for f, r in zip(fresh, recorded, strict=True))
        sample.rollout_log_probs = fresh
```

## 验证信号

训练/推理 logprob 一致性排查：用 .pt 回放固定样本，在重算 logprob 时逐元素 abs/signed diff（登记机制片段：），配合 --train-logprobs-only 测量开关（接线见来源结论 干跑验证）。


## 适用与失效边界

适用：训练/推理 logprob 一致性排查：用 .pt 回放固定样本，在重算 logprob 时逐元素 abs/signed diff（登记机制片段：），配合 --train-logprobs-only 测量开关（接线见来源结论 干跑验证）。失效边界：验证止于 --dry-run 接线检查（开关只增不改默认路径），完整回放运行与差异归因结论未在轨迹内展示。
