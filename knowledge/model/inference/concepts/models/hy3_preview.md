---
type: Concept
title: Hy3：GQA、共享专家与当前 PA/MTP 接入
description: 正式Hy3的当前packed/PA、FP8 QKV融合、SP精确条件、共享专家多流和已接入MTP；纠正旧preview实现。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modules/common.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hy3/hy3_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/agentic/optimization_report.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_a3/hy3_rank16_bf16_mtp.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_950/hy3_rank4_mxfp4_mtp.yaml
  role: example
created_at: '2026-05-31T00:00:00Z'
updated_at: '2026-10-29T14:28:49Z'
platforms:
- a3
- '950'
---

# Hy3：GQA、共享专家与当前 PA/MTP 接入

## 结构

当前正式Hy3为295B总参、约21B激活，80层主干加1层MTP。首层Dense FFN，后79层MoE；hidden4096，64Q/8KV heads、head_dim128，192 routed experts/top8及1个shared expert，词表120832，最大上下文262144。QK Norm按head，路由为FP32 sigmoid/top-k并使用校正bias和缩放2.826。

Dense intermediate13312、专家1536；与Qwen3-MoE区别是共享专家与sigmoid路由。当前路径models/hy3，旧preview路径不再使用；保留本卡Concept链接以兼容已有导航。

## 当前 packed 与 Page cache

主干使用packed [T,H]/1D position_ids，CacheEntry/get_cache_info接入FullAttention Page cache，要求slot_mapping/block_table。BF16走TND FIA v2与scatter_nd写入；旧连续BSH、FA v1的基础报告描述不再代表当前模型。

FP8 KV由权重quantization_config.kv_cache_scheme触发：QKV预处理融合QK Norm/RoPE/rotation/量化与写回；cache布局BnNBsD，另有FP32 k_scale_cache。此路径硬要求head_dim128、block_size128和匹配cann_ops_transformer算子；FIA为NTD_TND，Q/K quant_mode3、V mode2，不能套用视频MXFP8模式6/8。

## 当前 SP、专家与多流

SP由custom_params.enable_sp显式开启，代码缺省False（README参数表写True，使用实际YAML/代码）。量化SP覆盖MXFP4/原生FP8的特定gmm模式；开启SP要求attn_dp_size=1，量化Decode每DP batch还须≥attn_tp且整除它。MX路径传动态MXFP8值与scale，原生FP8按目标Linear静态scale量化仅传值，不混同。

Prefill AG-RS路由要求EP>1、token确实在EP成员间分片、attn_tp==EP且top_k>EP，不是单有并行度相等。其他Prefill可走EP统一chunk数的DoubleRouting；空token返回空输出。纯EP Decode使用MC2，buffer按真实每rank请求及MTP宽度预算。

共享专家多流需enable_multi_streams且dense_tp=1，并核对SP/shared路径条件；A3当前配置关闭、950开启。源码用stream/event和record_stream维护生命周期，不能沿用旧“所有多流未落地”的结论。

## 当前 MTP

主模型跳过layer80仅是主干加载规则；HYV3ModelMTP独立加载该层及enorm/hnorm/eh_proj/final_layernorm，且不继承跳过规则。三份当前配置均next_n=1，不能再声称模型有MTP但部署没实现。主干返回hidden供draft使用，主/草稿cache索引分开，验证Decode保留next_n+1宽度。

[部署指南](../../guides/models/hy3_preview_deployment.md)与[A3基础报告观测](../../optimizations/benchmark_observations/hy3_a3_source_benchmark.md)区分当前配置与来源测量；本次未执行模型。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/README.md)（primary）
- [modeling_hy_v3.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py)（implementation）
- [common.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modules/common.py)（implementation）
- [hy3_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hy3/hy3_optimization.md)（supporting）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/agentic/optimization_report.md)（supporting）
- [hy3_rank16_bf16_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_a3/hy3_rank16_bf16_mtp.yaml)（example）
- [hy3_rank4_mxfp4_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_950/hy3_rank4_mxfp4_mtp.yaml)（example）
