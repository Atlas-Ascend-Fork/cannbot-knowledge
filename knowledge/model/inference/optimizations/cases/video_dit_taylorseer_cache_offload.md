---
type: Optimization
title: HunyuanVideo A3 TaylorSeer offload 案例：导数缓存与搬算流水
description: 当前TaylorSeer导数offload流依赖、统一配置和400GB来源提示，撤下无法绑定最新来源的旧估算与性能数。
tags:
- task.debugging
- topic.diffusion
- topic.memory
- topic.implementation.synchronization
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
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
---

# HunyuanVideo TaylorSeer：导数 offload 与搬算依赖

## 场景与当前入口

TaylorSeer为double block的img/txt attention与MLP、single block输出缓存多阶特征。当前统一sp8.yaml默认NoCache，可将dit_cache.method改TaylorSeer并设置params.offload=true；旧独立sp8_taylorseer.yaml不再存在。实算/预测计划见[选型规则](../rules/taylorseer_predictive_dit_cache.md)。

## 源码中的搬算流程

实算时先在当前流估计导数，copy_stream等待当前流后逐阶.to('cpu',non_blocking=True)，当前流再等待copy_stream。预测时copy_stream执行H2D，cal_stream等待对应copy_event后累加泰勒项；copy_stream还等待前一项cal_event避免覆盖，最后当前流等待cal_stream。

这些stream/event描述依赖关系和流水意图。non_blocking参数本身不证明主机页锁定、实际重叠比例或性能提升；应以真实时间线测量，而不能将源码存在多流等同于搬运已完全隐藏。

## 容量与来源边界

当前README明确提示720×1280×129开启TaylorSeer offload需400GB以上CPU内存。实际峰值还包含模型/采样器/VAE和暂存空间；不能将其作为所有卡数、阶数、分辨率的统一精确需求。

旧稿81.4GB、14.5MB及Free占比41.7→11.1/83.81→31.5来自历史材料，未在本次选定当前文件中找到，已撤下，不再与最新实现拼接成性能结论。本次未执行NPU或产生新的硬件测量。

## 验证与回退

在固定seed、采样器、规格下，对照NoCache验证生成质量，再分别测offload开关的主机/NPU峰值、D2H/H2D和计算时间线。当前Hunyuan允许多卡缓存入口，混合SP仍须按[通信组规则](../rules/dit_cache_with_sequence_parallel.md)核对。非NoCache与稀疏方法互斥。

容量不足先缩规格或NoCache；关闭offload仅在NPU能容纳导数时可行，不把旧“几乎必OOM”推成任意设备的结论。


## Evidence

- [cache_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/dit_cache/cache_method.py)（primary）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）
- [sp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml)（example）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md)（constraint）
