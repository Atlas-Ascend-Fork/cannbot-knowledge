---
type: Guide
title: HunyuanImage-3.0 A2/A3 并行接入与验收流程
description: HunyuanImage-3.0 A2/A3 并行接入与验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/README.md
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/ep8_cfg.yaml
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-22T10:38:03Z'
platforms:
- a2
- a3
---

# HunyuanImage-3.0 A2/A3 并行接入与验收流程

## 目标、输入与产物

面向固定来源中的 HunyuanImage-3.0 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/hunyuan_image_3.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 分开旧启动脚本和统一 YAML 入口

旧2f82d10文档对应 demo.sh；2c45117 的 infer.sh/config由统一多模态启动器驱动，不能混成同一版本。后者 ep8_cfg 的world_size16、Attention TP8、MoE EP8、CFG与VAE并行只作固定配置示例，具体分组需按实际卡/rank核对。入口 run_image_gen.py 的权重与图像输入输出先用基线跑通；启动机制见 [多模态启动](../../concepts/frameworks/mm_inference_launch.md)。

## 2. 优先复用并行规则

通用TP、Double-Routing、CFG、VAE空间并行分别读取 [TP](../../concepts/parallelism/tensor_parallel.md)、[路由机制](../../concepts/techniques/double_routing.md)、[CFG流程](../../optimizations/rules/cfg_parallel_sample_level_diffusion.md)、[VAE流程](../../optimizations/rules/vae_multicard_spatial_parallel.md)。本模型EP路径在QKV前AllGather、o_proj后ReduceScatter；MoE TP路径的共享专家与路由结果通信为另一种多流排布，不把两者当作同一组默认配置。

## 3. 平台分支与精度条件

固定 `2c45117` README 明确报告 `transformers==5.3.0` 存在精度问题，推荐 `5.2.0` 及以下版本。将该依赖条件纳入基线环境核对；这是该固定分支的来源记录，不推导其他实现或未来版本的精度边界。

AllGatherMM/MMReduceScatter都要检查2D输入、第0轴与模型展平顺序；按源码对应的 (s b) 排布变换并恢复输出，不能只照抄“s在最内侧”的文字推导索引。2c45117设备分支在Ascend910B使用普通reduce_scatter，非该分支才用MMReduceScatter融合；不能给A2宣称同样融合路径。

核对RoPE cos/sin的BF16转换、gate在禁用autocast后保留FP32、FA scale初始化，以及timestep_index移到循环外的透传。原文代码中的float与item写法需以实际源码调用为准，不直接复制缺括号片段。相关边界见 [DiT融合精度规则](../../optimizations/rules/precision_dit_fusion_autocast_cossin_dtype.md)。

## 4. 验证与数据缺口

对照同一prompt、seed、尺寸和采样步验收质量、端到端与显存，并分别测试A2回退和A3融合。固定优化文档未给可复用benchmark表或完整的推荐并行度，不新造收益。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)
- [固定来源 3](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/README.md)
- [固定来源 4](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/config/ep8_cfg.yaml)
- [固定来源 5](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)
