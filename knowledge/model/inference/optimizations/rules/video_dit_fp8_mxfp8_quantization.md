---
type: Optimization
title: 视频 DiT MXFP8 注意力与 Linear 量化决策
description: 按当前MXFP8注意力和Linear双开关分别验收950视频DiT，核对TND/量化轴、纯Ulysses、选层与offload控制变量。
tags:
- task.debugging
- topic.attention
- topic.diffusion
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fa_quant/fa_quant.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/unified_sp/core.py
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single_fp8.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/single.yaml
  role: constraint
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T12:28:04Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - dit
      quantization:
      - fp8
---

# 视频 DiT MXFP8 注意力与 Linear 量化决策

## 触发条件

当950上的视频DiT在BF16下受attention或Linear的显存/带宽限制时，分别评估动态MXFP8注意力和MXFP8 A8W8矩阵乘。当前HunyuanVideo两条路径采用独立开关，不预设跨模型的量化优先级。

## 注意力路径

当前使用 `npu_dynamic_mx_quant` 与FIA v2：Q/K按hidden维分组，mode6；V沿展平序列轴分组，mode8；数据E4M3FN、scale E8M0，TND输入与累计序列长度配套。旧的固定128/256块粒度、BNSD mode7以及 `fa_perblock_fp8` 已不对应当前代码。

使用 `fa_mxfp8=True` 时，UnifiedSPAttention拒绝Ring group size大于1，先确认单卡或纯Ulysses。当前attention封装为非稀疏模式，不自动承接任意causal/mask语义。详细接口见[MXFP8注意力](../../concepts/quantization/fp8_attention.md)。

## Linear路径

`dynamic_convert_mxfp8_linear` 只选择double_blocks/single_blocks内的Linear，跳过含mod的层与1D权重；这是源码选层策略，不是已经证明量化其他层必然损伤质量。

权重预量化、激活前向动态量化后调用 `npu_quant_matmul`，使用E8M0 scale及 `group_sizes=[1,1,32]`。`params_to_keep` 当前未被读取，无bias Linear和权重恢复需要额外处理，见[Linear量化](../../concepts/quantization/mxfp8_a8w8.md)。

## 配置与对照

当前配置入口为 `model_args.fa-mxfp8` 和 `model_args.mm-mxfp8`；随附 `config/single_fp8.yaml` 同时开启两者。其 `use-cpu-offload=false`，而 `single.yaml` 为true，因此直接比较这两个文件不能把全部差异归因于量化。

保持权重、输入、seed、步数、并行与CPU/VAE offload一致，按“都关、仅attention、仅Linear、两者同开”分别记录误差、画质、峰值内存和端到端时间。当前入口拒绝910B/910_93；量化FA需CANN9.1+。质量或净收益不通过时重载原始权重并关闭对应量化项。

## 相关入口

- [950接入案例](../cases/hunyuan_video_950_fp8_quantization.md)
- [来源观测](../benchmark_observations/hunyuan_video_950_source_benchmark.md)
- [HunyuanVideo部署](../../guides/models/hunyuan_video_deployment.md)
