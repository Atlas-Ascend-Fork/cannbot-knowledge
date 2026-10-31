---
type: Guide
title: HunyuanVideo 分版本的并行、稀疏与量化验收流程
description: 当前Hunyuan统一六类YAML、环境、权重、Ring稀疏/LSE与缓存/量化边界，去除跨版本混配。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/blockwise_sparse/sparse_method.py
  role: constraint
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-29T14:13:05Z'
platforms:
- a2
- a3
- '950'
---

# HunyuanVideo 当前部署与验收

## 环境与权重

当前README覆盖A2/A3/950，要求CANN9.1.0、PyTorch2.7.1、torch_npu 2.7.1.post3（扩展发布v7.3.1）、Python3.11。按对应设备准备依赖；上游HunyuanVideo代码以非覆盖方式合入适配目录，保存实际依赖版本。准备DiT、LLaVA-Llama3文本编码器及CLIP权重；文本编码器用hyvideo/utils/preprocess_text_encoder_tokenizer_utils.py拆分。

在models/hunyuan-video/config所选YAML中设置model_args.model-base，必要时dit-weight单独指定DiT checkpoint。CANN环境先source，项目PYTHONPATH仅由统一脚本给torchrun子进程设置。

## 选择当前配置

| YAML | 条件 |
| --- | --- |
| single.yaml | 单卡，dit_cache默认NoCache，可切FB/Tea/Taylor |
| single_fp8.yaml | 950 MXFP8 FA/A8W8；CPU offload与基线默认不同 |
| single_sparse.yaml | 单卡TopK/SVG |
| sp8.yaml | Ulysses8、VAE并行，缓存方法可切 |
| sp8_sparse.yaml | 多卡稀疏，默认Ulysses，可切Ring |
| sp8_sparse_overlap.yaml | Ring TopK overlap；SVG回退普通Ring SVG |

旧sp8_taylorseer.yaml、独立cache_config.json/sparse_config.yaml不再是当前主入口。稀疏参数放顶层sparse.method/params，缓存放dit_cache.method/params；两者同开当前入口会报错，应使用NoCache运行稀疏。

```bash
# 在模型目录中，修改infer.sh所选YAML或按其约定设置
export YAML_FILE_NAME=sp8.yaml
bash infer.sh
```

统一入口设置环境、日志res/<日期>/<模型>/并调用torchrun。模型参数true转flag、false省略、列表展开；要关闭默认值先核对argparse语义。检查日志中的最终参数和实际卡数。

## 并行与优化边界

world_size=ulysses-degree×ring-degree。标准模式按模型patch/latent尺寸与head整除核对；README链式取模表达式不能替代实际尺寸检查。UAA仅纯Ulysses，保留填充头数小于每卡新head数的边界。Hunyuan的VAE是宽度overlap-chunk decode，仍有宽度整除和感受野约束。

TopK先提取匹配视频规格的Q/K并离线profiling生成逐step/layer/head稀疏度，路径由sparse.params.TopK.sparsity_files_path设置；SVG为在线采样模式选择。先编译匹配SoC、CANN的blitz_sparse_attention及torch接口；Ring TopK overlap还要求LSE返回接口。升级CANN需重建。来源滚动算子依赖未绑定各表build，复现时另记录。

缓存的[SP组边界](../../optimizations/rules/dit_cache_with_sequence_parallel.md)仍须核对，不能把取消入口限制等同全部混合配置已验证。TaylorSeer offload在来源720×1280×129规格要求400GB以上主机内存。

950的fa-mxfp8/mm-mxfp8分别开FA与A8W8；FA仅单卡/纯Ulysses，不支持Ring。具体dtype、TND与版本要求见[量化指南](../../optimizations/rules/video_dit_fp8_mxfp8_quantization.md)。

## 验证与回退

先NoCache/no_sparse基线输出，固定seed/采样器/规格逐项开并行、缓存、稀疏和量化；检查质量、rank一致性、Host/NPU峰值、DiT/VAE/E2E与重复统计。prof-dit开启.prof分析。来源性能见[A3](../../optimizations/benchmark_observations/hunyuan_video_a3_source_benchmark.md)、[950](../../optimizations/benchmark_observations/hunyuan_video_950_source_benchmark.md)、[稀疏表](../../optimizations/benchmark_observations/hunyuan_video_sparse_source_observations.md)，本次未执行模型。

异常先关闭对应近似方法或overlap，恢复匹配规格、算子和并行基线；主机容量不足不能仅关Taylor offload就视为解决。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/README.md)（primary）
- [hunyuan_video_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hunyuan-video/hunyuan_video_optimization.md)（supporting）
- [sample_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/sample_video.py)（implementation）
- [sp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hunyuan-video/config/sp8.yaml)（example）
- [sparse_method.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/blockwise_sparse/sparse_method.py)（constraint）
