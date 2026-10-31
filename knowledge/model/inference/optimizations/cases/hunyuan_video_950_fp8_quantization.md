---
type: Optimization
title: HunyuanVideo 950 MXFP8 接入与验证案例
description: 使用当前single_fp8双量化开关，控制CPU offload差异，分别验收单卡/Ulysses量化质量、时延和恢复原权重的回退。
tags:
- task.optimization
- topic.diffusion
- topic.precision
status: stable
platforms:
- '950'
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single_fp8.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single.yaml
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fa_quant/fa_quant.py
  role: implementation
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
      quantization:
      - fp8
created_at: '2026-10-21T01:48:04Z'
updated_at: '2026-10-29T12:28:04Z'
---

# HunyuanVideo 950 MXFP8 接入与验证案例

## 当前配置

当前单卡配置 `models/hunyuan-video/config/single_fp8.yaml` 在 `model_args` 中同时设置 `fa-mxfp8=true` 与 `mm-mxfp8=true`，`dit_cache.method=NoCache`，720×1280、129帧、50步、seed42。

注意该配置 `use-cpu-offload=false`，基线 `single.yaml` 则为true。对照量化收益前需把offload、其余输入和生成参数调成一致；否则VAE/搬运路径变化会混入端到端结果。

## 接入与约束

FA使用当前TND动态MXFP8（Q/K mode6、V mode8），Linear使用MXFP8 A8W8，两条路径独立控制。旧的mode7 per-block实现已不在当前导出接口中。FA只允许单卡或纯Ulysses；不能由其他稀疏Ring功能推导量化FA支持Ring。入口限定950，FA依赖CANN9.1+。

在固定配置上分别测量两者都关、只开FA、只开Linear和同时开启；采用多卡时再独立验收Ulysses8，不把单卡结果外推。

## 验收与回退

保持权重、prompt、seed、采样步、分辨率/帧数、并行与offload一致，分别记录量化分支、图模式、视频质量、端到端与峰值内存。来源数据集中见[950观测](../benchmark_observations/hunyuan_video_950_source_benchmark.md)，没有统一量化画质保证。

Linear转换已改写权重数据，仅恢复 `original_forward` 不能撤回权重量化；回退应重载原始模型/权重并关闭相应开关。算子错误需检查完整异常链，FA版本提示不自动证明根因就是版本。本仓未运行硬件或质量复测。

## 相关入口

- [量化决策](../rules/video_dit_fp8_mxfp8_quantization.md)
- [MXFP8注意力](../../concepts/quantization/fp8_attention.md)
- [MXFP8 Linear](../../concepts/quantization/mxfp8_a8w8.md)
