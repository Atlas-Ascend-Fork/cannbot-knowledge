---
type: Optimization
title: FBCache 与 TeaCache：判据、状态与阈值验收
description: 最新FB/Tea公式、默认0.05/0.15、完整步参考更新、调用计数与已修复Tea属性，配套质量验收。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:09:27Z'
platforms:
- a2
---

# FBCache 与 TeaCache：判据、状态与阈值验收

## 适用条件与选择

已接入步间残差缓存的DiT，可用首块特征变化判断是否复用。NoCache是对照；阈值需按模型和目标质量标定，不能由一张速度表指定通用最优值。

| 方法 | 当前判据 | 默认阈值 |
| --- | --- | --- |
| FBCache | mean(abs(cur-prev))/(mean(abs(cur))+1e-8) | 0.05 |
| TeaCache | mean(abs(cur-prev))/(mean(abs(prev))+1e-8)，同步后经abs(poly1d(coefficients)(ratio))累加 | 0.15 |

低于阈值复用，Tea完整计算时清零累计量。两者参考特征和残差在完整计算后更新，因此不是每次都与紧邻上一采样步比较。命中返回上一完整计算残差加当前ori_latent。首尾强制实算由cnt/ret_steps控制，cnt是should_cache调用计数。

## 当前实现修正

TeaCache现在赋值和读取同一self.rel_l1_thresh，旧“第二步必然AttributeError、必须补丁或改FB”的结论不再成立；模块为module/dit_cache/cache_method.py。当前默认Tea阈值0.15，旧0.1不再是默认值。

统一YAML设置dit_cache.method和params；HunyuanVideo FB/Tea替换首个double block，非NoCache与稀疏方法互斥。不要照抄旧cache_config.json片段或旧dit_cache_step路径。

## 风险与验收

更大阈值通常允许更多复用，但实际命中序列受参考更新、多项式和累计重置影响，不能保证收益或质量单调。模型相关多项式不能直接迁移。CFG状态须[分槽](dit_step_cache_cfg_branch_slotting.md)，SP须[同步一致决策](dit_cache_with_sequence_parallel.md)。

分别记录NoCache/FB/Tea的输出质量、真实完整步数量、内存和端到端/DiT时间，固定软件和采样规格。当前优化文档保留来源实验表，不表示当前环境已复测；旧Tea属性缺陷也不应再用于否定当前实现。


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）
- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（supporting）
