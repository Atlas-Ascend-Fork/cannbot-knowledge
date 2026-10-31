---
type: Optimization
title: TaylorSeer：预测质量、导数缓存与当前配置
description: 当前TaylorSeer的步计划、统一sp8配置、实算/预测边界、400GB来源门槛与可验证回退。
tags:
- task.optimization
- topic.kv_cache
- topic.diffusion
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:09:27Z'
platforms:
- agnostic
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
---

# TaylorSeer：预测质量、导数缓存与当前配置

## 选择条件

DiT允许跨步近似且已有对应forward接入时，可将历史残差复用改为子模块特征预测。实算步用相邻activated_steps差分估计多阶导数，预测步计算Σ factor_i·x^i/i!；零步距会报错。更高阶和更长预测跨度不保证更准，必须与NoCache对照。

## 当前 Hunyuan 配置

在当前sp8.yaml修改dit_cache.method为TaylorSeer，params选择n_derivatives=3、skip_interval_steps=4、warmup=3、cutoff_steps=1、offload=true。默认方法仍为NoCache；旧sp8_taylorseer.yaml已移除。

step<warmup、(step-warmup)%skip_interval_steps==0或total_steps-step<=cutoff_steps时实算，其余预测。默认间隔4意味着计划内实算1次、预测3次，首尾保护会改变总比例。层计数与实际double/single block数由运行入口传入，不能直接用其他模型层数。

当前入口不再拒绝多卡+缓存，但缓存与TopK/SVG稀疏互斥；预测计划一致并不能证明任意模型/并行接入正确。Wan当前block只接FB/Tea，不将TaylorSeer列为已支持。

## 内存与回退

Hunyuan缓存所有接入block的多阶特征，默认offload=true；README对720×1280×129规格明确要求400GB以上CPU内存。该门槛限来源规格，不能替代实际峰值预算。旧81.4GB/14.5MB估算与Free占比数据未在当前绑定文件找到，已撤下。

先测主机/NPU峰值、预测误差和搬运开销；内存不足可减规格、减阶/跨度或回NoCache。仅关闭offload会把导数驻留转回NPU，不能自动解决容量不足。[当前offload案例](../cases/video_dit_taylorseer_cache_offload.md)说明实际流依赖。


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）
- [sp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml)（example）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md)（constraint）
