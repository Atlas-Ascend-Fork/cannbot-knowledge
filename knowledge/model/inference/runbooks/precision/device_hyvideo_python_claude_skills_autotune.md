---
{
  "type": "Runbook",
  "title": "hunyuan-video FBCache rel_l1_thresh=0.02 过 L0 性能门禁但 L1 质量门禁被单一 prompt（p24）击穿",
  "description": "模型/任务：cann-recipes-infer hunyuan-video（t2v-14B 文生视频），autotune-evaluator skill 的 FBCache 步间缓存加速 trial_006 评测（source 0 seq 1、seq 26）。",
  "tags": [
    "task.testing",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# hunyuan-video FBCache rel_l1_thresh=0.02 过 L0 性能门禁但 L1 质量门禁被单一 prompt（p24）击穿

## 适用场景

- 模型/任务：cann-recipes-infer hunyuan-video（t2v-14B 文生视频），autotune-evaluator skill 的 FBCache 步间缓存加速 trial_006 评测（source 0 seq 1、seq 26）。
- 环境：Ascend NPU 单卡（pick_free_device 实选 device 2）、conda env hyvideo、fp16、torch_npu transfer_to_npu；L0 负载 320x480x65、50 infer steps（source 0 seq 31、seq 32）。
- 评测协议：L0 性能+sanity 门禁（eval_l0_perf.py + check_video_sanity.py + aggregate_l0.py）；L1 逐 prompt LPIPS/SSIM 对 baseline 视频（compute_lpips_ssim.py + aggregate_l1.py，阈值 lpips 0.15 / ssim 0.85）（source 0 seq 34/37/67）。

## 触发与观测

- 尝试配置（source 0 seq 26，逐字）：

```json
{
    "cache_forward": "FBCache",
    "comment": "FBCache autotune trial_006 — rel_l1_thresh=0.02, testing lower threshold to fix prompt-0 and prompt-24",
    "enable_separate_cfg": true,
    "FBCache": {
        "cache_name": "FBCache",
        "rel_l1_thresh": 0.02,
        "latent": "latent",
        "judge_input": "cache_latent"
    },
```

- L0 通过（source 0 seq 38/40，tool_observed）：`feasible=True speedup=1.5423 sanity_passed=True`；trial_e2e_ms=69791.02 vs baseline_e2e_ms=107638.96，peak 显存 40.754GB，per_step 缓存命中步 ~26-28ms、未命中步 ~1258-1296ms。
- L1 失败（source 0 seq 65/68/70，tool_observed）：`feasible=False [FAIL (2 violation(s))]`，violations 逐字：

```json
"violations": [{"label": "24", "metric": "lpips", "threshold": 0.15, "value": 0.349868}, {"label": "24", "metric": "ssim", "threshold": 0.85, "value": 0.776572}]
```

## 探针与操作

- L0 运行命令（source 0 seq 31，逐字，脱敏路径）：

```bash
DEVICE=$(conda run -n hyvideo python .claude/skills/autotune-evaluator/scripts/pick_free_device.py) && \
ASCEND_RT_VISIBLE_DEVICES=$DEVICE conda run -n hyvideo --no-capture-output \
  python eval_l0_perf.py \
  --prompt "a car accelerating to gain speed" \
  --seed 61724 \
  --video-size 320 480 \
  --video-length 65 \
  --model-base ${PRIVATE_PATH_6} \
  --output autotune_test/results/trial_006/l0_perf.json \
  --save-video autotune_test/results/trial_006/l0_video.mp4 \
  --cache-config autotune_test/trial_configs/trial_006_config.json
```

- L1 指标（source 0 seq 65，逐字）：

```
OK p00: [DONE] mean_lpips=0.0670  mean_ssim=0.9178
OK p01: [DONE] mean_lpips=0.0728  mean_ssim=0.8813
OK p02: [DONE] mean_lpips=0.0091  mean_ssim=0.9753
OK p24: [DONE] mean_lpips=0.3499  mean_ssim=0.7766
OK p25: [DONE] mean_lpips=0.0188  mean_ssim=0.9429
```

- L1 聚合（source 0 seq 67）：`aggregate_l1.py --labels 0 1 2 24 25 --lpips-threshold 0.15 --ssim-threshold 0.85 --lpips-max 0.3 --ssim-min 0.7`。

## 机制与判别

- 判别事实：质量退化高度集中在单一 prompt——p24（"Origami dancers in white paper, 3D render, on white background..."）lpips 逐帧 0.330-0.371 全程偏高、ssim 0.744-0.803；其余 4 prompt lpips≤0.0728、ssim≥0.8813，p02 甚至 lpips 0.0091/ssim 0.9753。即 FBCache 失真不是均匀噪声，而是对特定视觉内容（白背景纸偶、细节纹理）系统性放大。
- 阈值演进：config 注释明示 0.02 是在前序更高阈值试验暴露 prompt-0/prompt-24 越界后继续下调的取值，仍未能救回 p24；说明该 prompt 的失真对 rel_l1_thresh 在 ≥0.02 区间不敏感（继续微调收益存疑，未验证）。
- 速度面：缓存命中步 ~27ms vs 未命中 ~1260ms，速度收益与质量击穿同源于"跳过 DiT 前向"的缓存命中判定；L0 sanity（帧数/NaN/冻结/闪烁）对这种内容级失真不敏感，只有逐 prompt 感知指标能拦截。

## 验证信号

- tool_observed：L0 聚合与 l0_detail.json（seq 38/40）、L1 逐对指标输出（seq 65）、l1_detail.json violations（seq 68/70）、tuning_state.yaml 写回与固定格式摘要 `trial_006 | L0=feasible speedup=1.54 | L1=fail lpips_mean=0.10 ssim_mean=0.90`（seq 73/74）。
- 验证层次：source_read + end_to_end（真实端到端视频生成 + 与 baseline 的感知指标对比）；L0 速度为单次运行本次观测。

## 适用与失效边界

- 适用：hunyuan-video 类扩散视频模型在 NPU 上做 FBCache/TeaCache 步间缓存调参时，必须以逐 prompt 感知指标（LPIPS/SSIM）而非全局 sanity 或均值把关；均值（lpips_mean=0.1035）可被多数 prompt 掩盖，单 prompt 双指标越界才是真实判据。
- 失效/边界：本轨迹仅覆盖 rel_l1_thresh=0.02 单点；p24 类内容的失效阈值与更优缓存策略（分 prompt 自适应阈值、更换 judge_input）未探索；baseline l1 视频生成参数未在本轨迹内核对。
- 运行注意：L1 并行 5 worker 失败（exit 1，3/5 产出；OOM 归因为 agent 叙述），串行 + pick_free_device 可靠；单次运行结论，采纳前应重复测量并在 1280*720 目标分辨率复核（tuning_state 协议要求）。

## 附：断言存档

- 尝试与 L0 性能门禁（本次观测，单次运行）：trial_006 = FBCache rel_l1_thresh=0.02（enable_separate_cfg=true，judge_input=cache_latent），负载 320x480x65、prompt "a car accelerating to gain speed"、seed 61724、infer_steps 50、单卡（pick_free_device 选 device 2）；L0 聚合 feasible=True：trial e2e 69791.02ms vs baseline 107638.96ms（speedup=1.5423），sanity 全过（65/65 帧、无 NaN/Inf、无 frozen/flicker/solid_color，max_jump 0.0481<0.2），peak 显存 40.754GB；per_step 序列显示缓存命中步约 26-28ms、未命中步约 1258-1296ms。
- L1 质量门禁失败（客观失败）：5 个 VBench prompt（0/1/2/24/25，seed 各一）生成的 trial 视频与 baseline 视频逐对计算 LPIPS/SSIM：p24（"Origami dancers in white paper, 3D render, on white background, studio shot, dancing modern dance."）mean_lpips=0.349868（阈值 0.15）、mean_ssim=0.776572（阈值 0.85）双违反且逐帧 lpips 0.330-0.371 全程偏高；其余 4 prompt lpips 0.0091-0.0728、ssim 0.8813-0.9753。aggregate_l1 判 feasible=False（2 violations，均 label 24）；汇总 lpips_mean=0.1035、ssim_mean=0.8988，trial 结论 fail。trial_006_config 注释明示选 rel_l1_thresh=0.02（较前序 trial 更低）正是为修 prompt-0 与 prompt-24 的质量越界，仍未能救回 p24。

```text
DEVICE=$(conda run -n hyvideo python .claude/skills/autotune-evaluator/scripts/pick_free_device.py) && \
echo "Using device: $DEVICE" && \
ASCEND_RT_VISIBLE_DEVICES=$DEVICE conda run -n hyvideo --no-capture-output \
  python eval_l0_perf.py \
  --prompt "a car accelerating to gain speed" \
  --seed 61724 \
  --video-size 320 480 \
  --video-length 65 \
  --model-base ${PRIVATE_PATH_6} \
  --output autotune_test/results/trial_006/l0_perf.json \
  --save-video autotune_test/results/trial_006/l0_video.mp4 \
  --cache-config autotune_test/trial_configs/trial_006_config.json
```

```text
Computing metrics for prompt 0...
OK p00: [DONE] mean_lpips=0.0670  mean_ssim=0.9178
       detail → autotune_test/results/trial_006/l1/p00_metrics.json
Computing metrics for prompt 1...
OK p01: [DONE] mean_lpips=0.0728  mean_ssim=0.8813
       detail → autotune_test/results/trial_006/l1/p01_metrics.json
Computing metrics for prompt 2...
OK p02: [DONE] mean_lpips=0.0091  mean_ssim=0.9753
       detail → autotune_test/results/trial_006/l1/p02_metrics.json
Computing metrics for prompt 24...
OK p24: [DONE] mean_lpips=0.3499  mean_ssim=0.7766
       detail → autotune_test/results/trial_006/l1/p24_metrics.json
Computing metrics for prompt 25...
OK p25: [DONE] mean_lpips=0.0188  mean_ssim=0.9429
       detail → autotune_test/results/trial_006/l1/p25_metrics.json
```
