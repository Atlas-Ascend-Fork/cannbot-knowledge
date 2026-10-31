---
type: Concept
title: DiT 步间缓存：复用、预测与当前模型接入
description: 当前四类DiT缓存、统一YAML、实际模型接入、已修复TeaCache属性及SP/CFG/计数边界。
tags:
- task.optimization
- topic.attention
- topic.multimodal
- topic.diffusion
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py
  role: constraint
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T14:09:27Z'
platforms:
- a3
---

# DiT 步间缓存：复用、预测与当前模型接入

## 机制

多步去噪的跨步特征可能平滑变化，可复用历史残差或预测子模块输出以减少计算。当前公共模块提供 NoCache、FBCache、TeaCache、TaylorSeer；模型必须另行接入对应 forward，公共管理器能创建对象不等于所有模型支持全部方法。

FBCache先算首块，用其输出变化判断是否跳过余下块；TeaCache用首块调制输入的相对变化，经模型相关多项式重标定后累计；两者复用 previous_residual+ori_latent。参考输入和残差只在完整计算时更新，不能简化成总与上一采样步比较。

TaylorSeer在实算步对各子模块特征做有限差分，记录多阶导数，预测步计算 Σ factor_i·x^i/i!。它缓存多个层和阶数，内存成本明显不同于整段残差复用；提高阶数不保证输出更准。

## 当前配置与接入

优先使用统一YAML的 dit_cache.method/params。加载器复制所有方法默认值，只合并选中方法参数；默认NoCache，enable_separate_cfg默认True。legacy JSON仍可加载，但必须包含cache_forward、enable_separate_cfg及四种方法配置，不能直接使用缺字段的旧摘录。

HunyuanVideo将TaylorSeer接入全部double/single block；FB/Tea只替换首个double block。当前入口不再硬拒绝多卡+缓存，但非NoCache与TopK/SVG稀疏互斥。Wan2.2-I2V接入的是FB/Tea分支，多卡会强制替换NoCache；不能把公共TaylorSeer自动视为Wan已接入。

## 状态与并行边界

- [阈值规则](../../optimizations/rules/dit_step_cache_fbcache_teacache.md)：当前TeaCache阈值属性已一致，旧属性名崩溃结论撤销。默认阈值FB0.05、Tea0.15。
- [SP一致性](../../optimizations/rules/dit_cache_with_sequence_parallel.md)：数据相关决策需要所有相关通信rank一致；当前Ulysses组绑定不能证明混合Ring正确。
- [CFG分槽](../../optimizations/rules/dit_step_cache_cfg_branch_slotting.md)：串行cond/uncond隔离状态；固定分支进程不应直接交替槽位。
- [TaylorSeer选型](../../optimizations/rules/taylorseer_predictive_dit_cache.md)：核对预测误差、导数内存和offload。

FB/Tea的cnt按should_cache调用递增，首尾ret_steps默认2；CFG串行时不能无条件解释成每个分支各前后两个去噪step。TaylorSeer有独立warmup/cutoff计划。

## 验证与入口

固定模型、采样器、seed、规格与平台，对照NoCache验证生成质量、各分支命中、跨卡路径一致、内存和稳态耗时。本次未运行NPU，也未增加verified。

- [HunyuanVideo部署](../../guides/models/hunyuan_video_deployment.md)
- [Wan2.2部署](../../guides/models/wan2_2_i2v_deployment.md)
- [CFG Parallel](../parallelism/cfg_parallel.md)
- [Hunyuan3D](../../../spatial/concepts/models/hunyuan3d.md)


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）
- [cache_block.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/wan/cache/cache_block.py)（implementation）
- [generate.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/wan2.2-i2v/generate.py)（constraint）
