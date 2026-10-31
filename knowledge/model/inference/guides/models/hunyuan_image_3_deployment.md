---
type: Guide
title: HunyuanImage-3.0 A2/A3 并行接入与验收流程
description: 当前HunyuanImage的统一YAML、CFG每rank缓存修正、融合布局、A2回退与实际精度/稳态验收边界。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/config/ep8_cfg.yaml
  role: example
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-29T14:17:52Z'
platforms:
- a2
- a3
---

# HunyuanImage-3.0 A2/A3 并行接入与验收流程

## 目标、输入与产物

面向固定来源中的 HunyuanImage-3.0 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/hunyuan_image_3.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 使用当前统一YAML

infer.sh/config由统一多模态启动器驱动。当前ep8_cfg的world_size16，Attention TP8/MoE EP8并开启CFG与VAE并行；先按实际rank核对分组和切分后权重。入口为run_image_gen.py，设置model-id、prompt、seed、图像尺寸与diff-infer-steps。机制见[多模态启动](../../concepts/frameworks/mm_inference_launch.md)。旧demo.sh与旧版本对照不再作为当前流程。

## 2. 优先复用并行规则

通用TP、Double-Routing、CFG、VAE空间并行分别读取 [TP](../../concepts/parallelism/tensor_parallel.md)、[路由机制](../../concepts/techniques/double_routing.md)、[CFG流程](../../optimizations/rules/cfg_parallel_sample_level_diffusion.md)、[VAE流程](../../optimizations/rules/vae_multicard_spatial_parallel.md)。本模型EP路径在QKV前AllGather、o_proj后ReduceScatter；MoE TP路径的共享专家与路由结果通信为另一种多流排布，不把两者当作同一组默认配置。

## 3. 平台分支与精度条件

当前README 明确报告 `transformers==5.3.0` 存在精度问题，推荐 `5.2.0` 及以下版本。该 README 的环境组合为 CANN 9.0.0-beta.1、torch_npu v7.3.1、PyTorch 2.7.1 与 Python 3.11，其他组合需另行验证。将这些依赖条件纳入基线环境核对；这是该固定分支的来源记录，不推导其他实现或未来版本的精度边界。

AllGatherMM/MMReduceScatter都要检查2D输入、第0轴与模型展平顺序；按源码对应的 (s b) 排布变换并恢复输出，不能只照抄“s在最内侧”的文字推导索引。当前设备分支在Ascend910B使用普通reduce_scatter，非该分支才用MMReduceScatter融合；不能给A2宣称同样融合路径。

核对RoPE cos/sin的BF16转换、gate在禁用autocast后保留FP32、FA scale初始化，以及timestep_index移到循环外的透传。原文代码中的float与item写法需以实际源码调用为准，不直接复制缺括号片段。相关边界见 [DiT融合精度规则](../../optimizations/rules/precision_dit_fusion_autocast_cossin_dtype.md)。

## 4. 当前缓存与布局修正

当前CFG并行时StaticCache和position_ids按每rank batch_size分配；非CFG并行才乘cfg_factor，不应保留旧先加倍再按rank切位置的实现。Attention的文本/图像/时间步切片现显式contiguous后进入融合算子，迁移时保留布局处理。

README建议质量检查可先跑1轮，稳态测量建议8轮以上；建议不等于已处理所有warmup。profiling修改对象为adaptor_patches/hunyuan_image_3_pipeline.py，idx_round>1才启用时需核对计数起点，保存实际采集轮次。

## 5. 验证与数据缺口

对照同一prompt、seed、尺寸和采样步验收质量、端到端与显存，并分别测试A2回退和A3融合。固定优化文档未给可复用benchmark表或完整的推荐并行度，不新造收益。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/README.md)（primary）
- [hunyuan_image_3_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-image-3.0/hunyuan_image_3_optimization.md)（supporting）
- [hunyuan.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/adaptor_patches/hunyuan.py)（implementation）
- [ep8_cfg.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-image-3.0/config/ep8_cfg.yaml)（example）
