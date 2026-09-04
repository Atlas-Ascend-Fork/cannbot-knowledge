---
type: Optimization
title: step-level DiT 跳步缓存遇 CFG 串行双分支 — 缓存状态必须按 guidance 分支分槽，否则 cond/uncond 互相覆盖残差
description: 单卡 dit 视频生成，用 step-level 跳步缓存（dit-cache 的 FBCache / TeaCache 这类"相邻采样步判据张量差异小→跳整步、复用上一步残差"）加速，而模型又用 Classifier-Free Guidance（CFG）、且 cond / uncond 两分支串行灌进同一个被 monkey-patch 的首块 forward。这是 step-cache + CFG 串行结构的通用陷阱，不限于某一模型：只要缓存实现按"单份状态"写，就会在这种结构下出错。残差复用型缓存的键控/阈值细节见 dit-step-cache-fbcache-teacache；想更激进跳步见 taylorseer-predictive-dit-cache。
tags:
- task.optimization
- topic.diffusion
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/240
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# step-level DiT 跳步缓存遇 CFG 串行双分支 — 缓存状态必须按 guidance 分支分槽，否则 cond/uncond 互相覆盖残差

## 适用场景

单卡 [dit](../../../concepts/modules/dit.md) 视频生成，用 step-level 跳步缓存（[dit-cache](../../../concepts/techniques/dit_cache.md) 的 FBCache / TeaCache 这类"相邻采样步判据张量差异小→跳整步、复用上一步残差"）加速，**而模型又用 Classifier-Free Guidance（CFG）、且 cond / uncond 两分支串行灌进同一个被 monkey-patch 的首块 forward**。这是 step-cache + CFG 串行结构的通用陷阱，不限于某一模型：只要缓存实现按"单份状态"写，就会在这种结构下出错。残差复用型缓存的键控/阈值细节见 [dit-step-cache-fbcache-teacache](dit_step_cache_fbcache_teacache.md)；想更激进跳步见 [taylorseer-predictive-dit-cache](taylorseer_predictive_dit_cache.md)。

## 问题信号

- 开了 CFG 且用 step-cache 后，生成质量崩坏 / 出现分支干扰，但关掉 CFG 或关掉缓存就正常。
- 根因：step-cache 若只保存**单份**缓存状态（`prev_block` / `previous_residual` / `accumulated_rel_l1` 各一个），在 CFG 串行双分支下失效——cond 与 uncond 交替进入同一首块 forward、交替调用 `should_cache` / `reuse_cache`，会互相覆盖对方的 `prev_block` / 残差，并把两分支的 rel-L1 累加混在一起：判据被另一分支状态污染，复用到错误残差。

## 做什么

**缓存状态按 guidance 分支分槽**（可迁移手段）：

### 1. 每个缓存张量拆成 `[uncond, cond]` 两槽，所有读写按分支索引

```python
def reuse_cache(self, is_cond: bool = True) -> torch.Tensor:
    idx = 1 if is_cond else 0
    return self.previous_residual[idx] + self.ori_latent
```

`prev_block` / `prev_judge_input` / `previous_residual` / `accumulated_rel_l1` 全部改为 `[None, None]` / `[0.0, 0.0]` 双槽，`should_cache` / `reuse_cache` / `cache_update` 同理按 `idx = 1 if is_cond else 0` 取用与更新。

### 2. 分支归属由首块 forward 内一个每次调用翻转的计数决定

```python
is_cond = (self.cfg_step == 0)    # 开启分离时首次视为 cond；关闭则 is_cond 恒 True
self.cfg_step = 1 - self.cfg_step
```

把 `is_cond` 随判据一起传进缓存的 `pre_cache_process`，并记入 `last_is_cond` 供跳步后回写正确分支槽。

### 3. 跳步早返回后须复位

判据命中"可复用"时置 `should_skip`、直接返回复用 latent，跳过本 step 剩余全部 DiT block；**一个 step 全部 block 跑完后须复位 `should_skip = False`**，避免跨 step / 跨分支残留。

## 前置条件 / 何时不适用

- 前置：该分支分槽仅在配置显式开启 CFG 分离时生效（参考实现用一个 `enable_separate_cfg` 开关）；关闭时 `is_cond` 恒 True、行为退回原单份缓存。
- 不走 CFG 分离的模型（cond/uncond 不串行进同一 patched forward，如 HunyuanVideo 该形态）无此问题，退化为单分支单份缓存——无需分槽。
- 参考实现约束：仅覆盖单卡（DiT-Cache 与多卡序列并行互斥，见 [taylorseer-predictive-dit-cache](taylorseer_predictive_dit_cache.md)）。

## correctness 验证 / 风险

- 验证：CFG 串行双分支下 cond / uncond 各自维护独立缓存与 rel-L1 累加、互不干扰，使 step-level cache 可正确用于 Wan2.2-I2V 这类 CFG 串行模型。源未给该适配前后的性能/精度对照数字。
- 风险边界：结论覆盖 step-cache（rel-L1 判据跳步）+ CFG 串行双分支这一结构；具体开关名 / 默认值 / `cfg_step` 翻转逻辑为参考实现（cann-recipes-infer 的 [wan2.2-i2v](../../../concepts/models/wan2_2_i2v.md)）当前形态，不外推为算子 / 框架合约。

## 相关经验

- 另见 [在 NPU 上对含 1×1 卷积的 DiT 做 MXFP 低比特量化 — 卷积当线性算·加载期模块替换 + a4w4 混合精度部分回退 a8w8](dit_mxfp_lowbit_quant_conv_as_linear.md)。


## Evidence

- **diff 事实**（clone `@79de4ef93dcb`）：`module/dit_cache_step/cache_step.py` 中 `prev_block` / `prev_judge_input` / `previous_residual` / `accumulated_rel_l1` 均改为 `[None,None]` / `[0.0,0.0]` 双槽 + `idx = 1 if is_cond else 0` 索引；`StepCache.reuse_cache(is_cond)`；`models/wan2.2-i2v/wan/cache/cache_block.py` 首块 forward 的 `cfg_step` 翻转 + `is_cond` 传参 + skip 早返回。归因主语为 cann-recipes-infer 对共享 dit-cache 模块的适配。
- 溯源下探：[cann-recipes-infer-pr-240-feat-hunyuanvideo-wan2-2-step-level-cache-cfg](https://gitcode.com/cann/cann-recipes-infer/merge_requests/240)

<!-- cannbot:related:start -->
## 相关

- [DiT Cache (FBCache / TeaCache / TaylorSeer)](../../../concepts/techniques/dit_cache.md)（`related`）：CFG 缓存约束为“**CFG 必须分离**：cond/uncond 共享 cache 会导致跳步判断错位”，故障触发条件为“cond 与 uncond 交替进入同一首块 forward”并要求双槽状态；它把概念约束推进到故障信号、分槽实现和复位验证。
- [Wan2.2-I2V](../../../concepts/models/wan2_2_i2v.md)（`related`）：“集成 ［FBCache］(https://github.com/chengzeyi/ParaAttention)、［TeaCache］(https://liewfeng.github.io/TeaCache/)。因 WAN2.2 CFG 串行特点，采用 ［TeaCache4Wan2.1 cond/uncond 分别管理版］(https://github.com/ali-vilab/TeaCache/tree/7c10efc4702c6b619f47805f7abe4a7a08085aa0/TeaCache4Wan2.1)。实现路径：`module/dit_cache_step/cache_step.py` + `wan/cache/cache_block.py`。”与“单卡 ［dit］(../../../concepts/modules/dit.md) 视频生成，用 step-level 跳步缓存（［dit-cache］(../../../concepts/techniques/dit_cache.md) 的 FBCache / TeaCache 这类"相邻采样步判据张量差异小→跳整步、复用上一步残差"）加速，**而模型又用 Classifier-Free Guidance（CFG）、且 cond / uncond 两分支串行灌进同一个被 monkey-patch 的首块 forward**。这是 step-cache + CFG 串行结构的通用陷阱，不限于某一模型：只要缓存实现按"单份状态"写，就会在这种结构下出错。残差复用型缓存的键控/阈值细节见 ［dit-step-cache-fbcache-teacache］(dit_step_cache_fbcache_teacache.md)；想更激进跳步见 ［taylorseer-predictive-dit-cache］(taylorseer_predictive_dit_cache.md)。”。模型卡要求 TeaCache 分开管理 cond/uncond，经验卡给出双分支覆盖状态的故障机制和分槽修复。
- [DiT 采样步残差缓存（FBCache / TeaCache）键控、阈值权衡与 TeaCache 属性名 bug](dit_step_cache_fbcache_teacache.md)（`same_topic`）：“cond 与 uncond 交替进入同一首块 forward、交替调用 `should_cache` / `reuse_cache`，会互相覆盖对方的 `prev_block` / 残差”指出 CFG 串行分支的污染点；“复用时 `reuse_cache()` 返回 `previous_residual + ori_latent`，`post_cache_update` 以 `latent - ori_latent` 更新残差”给出被污染状态的生产与消费位置。
<!-- cannbot:related:end -->
