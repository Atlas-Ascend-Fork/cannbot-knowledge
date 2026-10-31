---
type: Guide
title: Qwen3-MoE 当前自研与 SGLang 部署
description: 当前A3/950与SGLang分立部署、三类量化/Hadamard、精确Prefill门控及已迁移的统一入口和缓存。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_moe/qwen3_moe_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_4tp_4ep_quant.yaml
  role: example
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/README.md
  role: constraint
created_at: '2026-10-21T09:56:20Z'
updated_at: '2026-10-29T14:21:59Z'
platforms:
- a3
- '950'
---

# Qwen3-MoE 当前自研与 SGLang 部署

## 先选实现与平台

自研models/qwen3_moe与integration/sglang/qwen3-moe是独立路径。自研当前README覆盖A3与950：A3 CANN9.0.0，950 CANN9.1.0-beta.1，均列PyTorch2.8.0/torch_npu2.8.0.post4（发布26.0.0）与Python3.11。SGLang依其README/分阶段patch验收，不混用权重、MTP、编译缓存或基准。

## 当前入口与量化配置

统一入口bash executor/scripts/infer.sh --model qwen3_moe --yaml <文件>。在线另选--mode online --pd-role及--p-yaml-name/--d-yaml-name，PD默认目录qwen3_moe_pd。按实际YAML核对world_size、Attention TP/DP与MoE TP/EP和卡数。

950当前支持三种转换：默认W4A8 MXFP8；--quant_type w4a4c16配合Hadamard；--quant_type w8a8hif8_w4a8mxfp采用Attention HiF8和MoE MXFP4/MXFP8。前后两种可共用qwen3_235b_4tp_4ep_quant.yaml，真实量化来自权重config.quantization_config，不能由YAML文件名判断。

Hadamard使用qwen3_235b_mxfp4_hadamard.yaml，转换与运行都需匹配hadamard_weight_path及每层layer_<idx>_self_attn.pt。仅Attention A4W4且enable_hadamard时进入，缺目录或层文件会失败；不能在W4A8档开flag就声称启用。

## Prefill与缓存实现核对

最新[模型机制](../../concepts/models/qwen3_moe.md)明确prefill_opt还要求两种特定MX量化模式，HiF8方案虽共用YAML也不满足相同条件。Prefill先AllGather量化数据和scale，FA后AlltoAll再o_proj；MoE用AG+RS，其余路径仍按TP/DoubleRouting/Decode MC2分派。

当前模型packed position_ids必须1D；Prefill按累计有效长度取末token，Page cache由CacheEntry声明block_size。FP8 KV包含独立scale缓存。来源旧Qwen3MoeRunner/./compile_cache/CASE_NAME片段已过时，按共享执行器实际output_path/compile_cache与图模式核对。force_eplb只作性能实验，会改变路由，质量验收关闭。

## SGLang与验收

SGLang按当前集成README核对基础NPU/量化、profiler、GE、MTP及SuperKernel各阶段patch；[SuperKernel案例](../../optimizations/cases/qwen3_moe_a3_superkernel_scopes.md)说明范围，不能将自研950分支外推该实现。

当前优化文档概述A3八卡BF16 Decode<20ms、950四卡W4A8的4K Prefill<280ms/Decode<24ms；缺完整逐轮记录，不当作本机复现或任意规格保证。两条A3来源结果另见[观测](../../optimizations/benchmark_observations/qwen3_moe_a3_source_benchmark.md)。

固定prompt、模型、软件和并行，分别对照BF16/目标量化、eager/图模式和Prefill/Decode，验质量、缓存布局、shape与真实命中；异常时恢复匹配原权重和基线配置。本次未运行NPU。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/README.md)（primary）
- [modeling_qwen3_moe.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/models/modeling_qwen3_moe.py)（implementation）
- [qwen3_moe_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/qwen3_moe/qwen3_moe_optimization.md)（supporting）
- [qwen3_235b_4tp_4ep_quant.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/qwen3_moe/config/qwen3_235b_4tp_4ep_quant.yaml)（example）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-moe/README.md)（constraint）
