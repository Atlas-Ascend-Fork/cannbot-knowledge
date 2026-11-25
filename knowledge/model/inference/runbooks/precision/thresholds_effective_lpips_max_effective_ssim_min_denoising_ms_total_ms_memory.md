---
{
  "type": "Runbook",
  "title": "Hunyuan-Video t2v-14B NPU cache 加速（TaylorSeer/FBCache/TeaCache）：L0 加速与 sanity 全过但 L1 感知质量门全败，复杂静态背景 prompt 系统性超限",
  "description": "Hunyuan-Video t2v-14B 文生视频推理（cann-recipes-infer models/hunyuan-video），单卡 NPU（pick_free_device 分配，conda env hyvideo，torch_npu），固定负载：320x480x65 帧、50 infer steps、embedded-cfg-scale 6.0、CPU offload。",
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

# Hunyuan-Video t2v-14B NPU cache 加速（TaylorSeer/FBCache/TeaCache）：L0 加速与 sanity 全过但 L1 感知质量门全败，复杂静态背景 prompt 系统性超限

## 适用场景

Hunyuan-Video t2v-14B 文生视频推理（cann-recipes-infer models/hunyuan-video），单卡 NPU（pick_free_device 分配，conda env hyvideo，torch_npu），固定负载：320x480x65 帧、50 infer steps、embedded-cfg-scale 6.0、CPU offload、固定 seed。优化目标：用 diffusion cache 方法（TaylorSeer/FBCache/TeaCache）加速推理，以 autotune-evaluator 的 L0（单 prompt 计时+sanity）/L1（5 prompt LPIPS/SSIM 质量门）两级评测筛选可行配置。

## 触发与观测

- baseline（NoCache）实测（source 2 seq 18，逐字）：`"e2e": {"denoising_ms": 64857.53, "total_ms": 107638.96}, "memory": {"peak_gb": 40.578}`。
- 4 组试验（每个 trial 独立会话，工具实测）：

| trial | 方法与参数 | L0 speedup | L1 结果 |
|---|---|---|---|
| 008（source 0） | TaylorSeer n_derivatives=3, skip_interval_steps=2, warmup=3 | 1.1993 | FAIL 3 违规 |
| 007（source 1） | TaylorSeer skip_interval_steps=4, warmup=3 | 1.5375（e2e 70010ms） | FAIL 7 违规 |
| 005（source 2） | FBCache rel_l1_thresh=0.05 | 2.0341 | FAIL 3 违规 |
| 004（source 3） | TeaCache rel_l1_thresh=0.07, warmup=5 | 1.641 | FAIL 2 违规 |

- L0 sanity（帧数 65/65、无 NaN/Inf、无冻帧/闪烁/纯色）在全部试验通过。

## 探针与操作

- L1 质量门阈值（source 0 seq 57 命令行，逐字）：`--lpips-threshold 0.15`、`--ssim-threshold 0.85`、`--lpips-max 0.3`、`--ssim-min 0.7`；逐 prompt 计算 LPIPS/SSIM（AlexNet LPIPS），trial 与 baseline 同 prompt 同 seed 对比。
- 代表性违规（工具 JSON 逐字）：
  - trial_008（source 0 seq 60）：`"violations": [{"label": "0", "metric": "lpips", "threshold": 0.15, "value": 0.179998}, {"label": "24", "metric": "lpips", "threshold": 0.15, "value": 0.351019}, {"label": "24", "metric": "ssim", "threshold": 0.85, "value": 0.773422}]`
  - trial_004（source 3 seq 63）：`"violations": [{"label": "24", "metric": "lpips", "threshold": 0.15, "value": 0.353582}, {"label": "24", "metric": "ssim", "threshold": 0.85, "value": 0.773777}]`
  - trial_007（source 1 seq 65）：`"lpips": {"0": 0.449698, "1": 0.1241, "2": 0.021809, "24": 0.318086, "25": 0.297709}`
  - trial_005（source 2 seq 63）：`"violations": [{"label": "0", "metric": "lpips", "threshold": 0.15, "value": 0.19741}, {"label": "24", "metric": "lpips", "threshold": 0.15, "value": 0.338176}, {"label": "24", "metric": "ssim", "threshold": 0.85, "value": 0.785348}]`

## 机制与判别

- 失败模式：加速比越大感知退化越重（skip=4 的 trial_007 比 skip=2 的 trial_008 违规从 3 处升至 7 处，p0 lpips 0.180→0.450）；但即便最保守的 TaylorSeer skip=2 也无法过门。
- prompt 内容主导边界：VBench prompt 24（Origami dancers in white paper, 3D render, on white background…）在 3 种方法、4 组参数下 lpips 0.318-0.354 全部超安全上限 0.3、ssim 0.773-0.802 全部低于 0.85，是唯一贯穿全部试验的违规点（lpips 每帧稳定 0.33-0.37，非个别帧尖刺）。TeaCache warmup 3→5（trial_004 vs trial_002，Agent 归纳）未改善该 prompt 退化（source 3 seq 70，agent_narrative）。
- 判别：sanity 检查（结构级）与 LPIPS/SSIM（感知级）结论完全脱钩——2.03x 加速的 FBCache sanity 全过而感知质量崩坏；评价 cache 加速必须包含感知级门禁。

## 验证信号

- 全部数值为工具输出（aggregate_l0/aggregate_l1/l1_detail.json，tool_observed）；每 trial 的 L0 为单 prompt 单次计时观测，无重复测量与统计口径；L1 为 5 prompt 单 seed 一次生成。
- Agent 声称 prompt 24 与 trial_003/005/006/007 历史规律一致（source 0 seq 64、source 3 seq 70，agent_narrative；历史 trial 数据不在本批证据内）。

## 适用与失效边界

- 适用：Hunyuan-Video t2v-14B 同负载（320x480x65f/50 步）下的 cache 加速可行性判断：在本批参数空间内（TaylorSeer skip 2-4、FBCache 0.05、TeaCache 0.07+warmup 5）没有任何配置同时满足加速与质量门；含白色/静态复杂背景类 prompt 的评测集会系统性判 FAIL。
- 失败不暗示方法本身不可用：更保守阈值、更长 warmup、prompt 感知的缓存策略或更大分辨率未测；本边界仅覆盖所列配置。
- L0 speedup 为单次观测且伴随质量门失败，不得作为可用加速收益引用；排除该负载/阈值组合需另行实验。

## 附：断言存档

- Hunyuan-Video t2v-14B 单卡 NPU（320x480x65 帧、50 infer steps、CPU offload；baseline 端到端 107638.96ms、峰值显存 40.578GB）上，4 组 diffusion cache 加速试验的 L0 性能层全部可行且视频 sanity（65 帧完整、无 NaN/Inf、无冻帧/闪烁/纯色）全部通过：TaylorSeer(n_derivatives=3, skip_interval_steps=2, warmup=3) speedup=1.1993；TaylorSeer(skip_interval_steps=4) speedup=1.5375（e2e 70010ms）；FBCache(rel_l1_thresh=0.05) speedup=2.0341；TeaCache(rel_l1_thresh=0.07, warmup=5) speedup=1.641（全部为 aggregate_l0 工具输出，单 prompt 单次计时观测）。
- 同一批试验的 L1 感知质量门（逐 prompt lpips≤0.15、ssim≥0.85，安全上限 lpips≤0.3/ssim≥0.7）全部失败：trial_008 3 处违规（p0 lpips 0.180、p24 lpips 0.351/ssim 0.773）；trial_007 7 处违规（p0 lpips 0.450/ssim 0.655、p24 lpips 0.318/ssim 0.802、p25 lpips 0.298/ssim 0.545）；trial_005 3 处违规（p0 lpips 0.197、p24 lpips 0.338/ssim 0.785）；trial_004 2 处违规（p24 lpips 0.354/ssim 0.774）。L0 加速与 sanity 通过不能外推感知质量（aggregate_l1/l1_detail.json 工具输出）。
- 失败边界由 prompt 内容主导：VBench prompt 24（Origami dancers，白色背景复杂静态场景）在 3 种方法（TaylorSeer/FBCache/TeaCache）、4 组参数下 lpips 0.318-0.354 全部超过安全上限 0.3 且 ssim 0.773-0.802 低于 0.85，是唯一在全部试验中持续违规的 prompt；TeaCache 将 warmup 3→5（trial_004 相对 trial_002）未改善该 prompt 退化（Agent 总结归纳，且各 trial 汇总声明与 trial_003/005/006/007 历史规律一致——历史 trial 不在本批证据内）。

```text
"thresholds": {"effective_lpips_max": 0.15, "effective_ssim_min": 0.85}
```
