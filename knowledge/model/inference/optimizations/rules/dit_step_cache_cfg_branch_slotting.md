---
type: Optimization
title: CFG 串行双分支的 DiT 缓存状态隔离
description: 当前CFG双槽读写、Wan交替接入、默认开关和共享调用计数；区分固定分支进程与模型集成边界。
tags:
- task.optimization
- topic.diffusion
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:09:27Z'
platforms:
- agnostic
---

# CFG 串行双分支的 DiT 缓存状态隔离

## 触发条件

同一patched首块交替处理cond/uncond时，单份参考特征、残差和Tea累计量会被另一分支覆盖。若CFG+缓存质量异常而NoCache正常，检查分支标识和状态槽，不应只增减阈值。

当前公共FBCache/TeaCache以idx=1 if is_cond else 0索引prev_block或prev_judge_input、previous_residual和accumulated_rel_l1。复用读取对应槽，再加本次ori_latent；完整计算更新同一槽。上层还须正确维护should_skip并在一轮所有block完成后复位。

## Wan 当前接入

Wan cache_block在首块维护cfg_step；enable_separate_cfg开启时按cond/uncond交替传入is_cond，并保留last_is_cond用于回写。当前YAML加载器的enable_separate_cfg默认True。关闭时统一使用cond槽，不能在确实串行双分支的路径上无条件关闭。

该逻辑假设调用顺序与两分支对应。每进程固定一路的CFG并行不能直接照搬cfg_step翻转；融合batch、改变分支顺序或额外首块调用时也须重新核对。公共FB/Tea的cnt仍是共享should_cache调用计数，分槽不等于每分支都有独立warmup计数。

Wan多卡入口当前强制NoCache。Hunyuan使用自己的block接入，不能将Wan交替CFG逻辑或“所有缓存仅单卡”的旧约束泛化过去。公共TaylorSeer类存在也不证明Wan实现了预测分支。

## 验证与回退

记录每次调用对应的真实分支、槽位、参考更新、skip与复位；对照无缓存输出并检查两分支累计量互不污染。调用模式不符时先NoCache，修正接入再评估质量和加速。来源未提供该分槽改造独立的质量/性能对照，本次未执行模型。

- [FB/Tea阈值](dit_step_cache_fbcache_teacache.md)
- [SP一致性](dit_cache_with_sequence_parallel.md)


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [cache_block.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py)（implementation）
- [generate.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py)（constraint）
