---
type: Guide
title: Hy3 A3/950 当前部署与 MTP 验收
description: 当前Hy3三类MTP配置、A3/950环境、FP8/AMCT权重、SP/PA/NZ和源码与旧基础报告差异。
tags:
- task.implementation
- topic.model_serving
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
created_at: '2026-10-21T09:56:18Z'
updated_at: '2026-10-29T14:28:49Z'
platforms:
- a3
- '950'
---

# Hy3 A3/950 当前部署与 MTP 验收

## 环境与权重

当前目录models/hy3。A3 README要求CANN9.1.0.beta.1、PyTorch2.8.0、torch_npu发布26.0.0；950提供x86 CANN9.1/PyTorch2.9专用镜像。两套环境分开准备，记录实际build与驱动。

A3使用Hy3 BF16；950可直接用Hy3-FP8，MXFP8+MXFP4从BF16用AMCT转换。当前README示例以hy_v3适配器、tensor粒度和moe/attn-linear/mlp目标转换，同时生成config；实际权重quantization_config必须匹配，不能靠输出目录名认定4bit。

## 当前三份 YAML

| 路径 | 配置 |
| --- | --- |
| ci_a3/hy3_rank16_bf16_mtp.yaml | A3 8卡16rank，attn/dense/embed/head TP4，MoE EP16，batch4，SP/多流关闭 |
| ci_950/hy3_rank4_mxfp4_mtp.yaml | 950四卡，Attention TP4、EP4、DenseTP1、batch4，SP/多流开启 |
| ci_950/hy3_rank4_fp8_mtp.yaml | 950原生FP8权重，按其实际YAML核对同类SP/MTP |

均next_n=1，默认npugraph_ex；A3输入400/输出128，MX配置InfiniteBench输入与Prefill预算65536。旧rank16_4tp_16ep_gegraph_bf16.yaml已撤下。按README在models/hy3设置可见设备后运行：

```bash
bash ../../executor/scripts/infer.sh --model hy3 --yaml ci_a3/hy3_rank16_bf16_mtp.yaml
```

各节点权重路径一致，IPs按rank排序；日志在models/hy3/res。数据集不存在时框架可能在线读取，离线部署先备齐数据。

## 关键实现约束

当前代码SP默认False，README表默认True不作为运行事实；以显式YAML为准。A3 dense_tp>1样例保持SP=False；量化SP要求Attention DP1及每DP batch为Attention TP的正倍数。FP8缓存还要求head_dim/block_size均128与已注册QKV融合算子。cache的布局/scale和paged metadata由共享管理器绑定，旧init_cache连续BSH方法仍留在类内，但不是当前get_cache_info部署路径。

MTP由独立类加载layer80和投影/归一化，主干忽略layer80不等于MTP不加载。验收时检查草稿权重、cache合并索引、接受率、回滚以及主/草稿宽度。MXFP4专家加载后必须按对应quant_method选择NZ，FP8专家保持ND；不能统一打开或关闭全部NZ。

多流仅在当前条件下启用共享专家重叠，缺省与README表有差异，不能由文字默认推定开启。来源基础报告中的旧BSH/FA v1、SuperKernel阶段和跳过MTP不应拿来解释当前代码；最新950指南展示PA/全FP8融合。

## 验证与来源测量

先固定权重、输入和软件验收No-MTP/eager，再分别开MTP、SP、图与多流；检查router top-k/权重、缓存布局、输出质量、Host/NPU峰值、接受率和真实Token口径。基础报告关于sigmoid/bias的质量判断不等于数学等价证明。

最新950指南的Offline TTFT表是batch1/四芯片、32K2330.23ms与64K7023.11ms；当前MX YAML却batch4，不能直接视为该YAML复现结果。A3基础报告另见[观测](../../optimizations/benchmark_observations/hy3_a3_source_benchmark.md)。本次未运行NPU；异常恢复匹配原权重、合法batch和基线配置。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/README.md)（primary）
- [modeling_hy_v3.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modeling_hy_v3.py)（implementation）
- [common.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/models/modules/common.py)（implementation）
- [hy3_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/hy3/hy3_optimization.md)（supporting）
- [optimization_report.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/agentic/optimization_report.md)（supporting）
- [hy3_rank16_bf16_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_a3/hy3_rank16_bf16_mtp.yaml)（example）
- [hy3_rank4_mxfp4_mtp.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/hy3/config/ci_950/hy3_rank4_mxfp4_mtp.yaml)（example）
