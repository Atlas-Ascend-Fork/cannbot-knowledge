---
type: Guide
title: GLM-5 当前部署：A3 W8A8 与 950 MXFP8
description: 更新GLM-5当前Docker/统一字段、A3与950配置，区分整数量化、MXFP8和被禁止的offload组合。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/utils/weight_convert.sh
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/ci_950/glm_5_w8a8mxfp8.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml
  role: implementation
created_at: '2026-10-21T09:56:17Z'
updated_at: '2026-10-29T15:05:36Z'
platforms:
- a3
- '950'
---

# GLM-5 当前部署：A3 W8A8 与 950 MXFP8

## 环境与权重

当前A3 README推荐包含CANN9.1/PyTorch2.8/自定义算子的ARM Docker镜像v0.2，宿主Ascend HDK25.2.0。各节点配置IP、CANN路径及原始GLM-5/GLM-5-FP8权重；离线与在线P/D节点列表分开填写。

在models/glm_5中source CANN后执行utils/weight_convert.sh：A3示例quant_mode=w8a8c16，950示例w8a8-mx，分别输出独立目录。脚本还保留w8a8c8/w4a8c8分支，但下载URL仍指DeepSeek-V3.2-Exp系数包，不能直接据参数存在认定GLM校准有效或已通过精度验收。

## 当前配置

| 路径（均相对config） | world/batch | 后端/平台 | CP/next_n | 主要用途 |
| --- | --- | --- | --- | --- |
| glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml | 64/64 | GE/A3 | 64/3 | W8A8 Prefill，o_projTP1/denseTP1 |
| glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml | 128/256 | GE/A3 | 128/3 | W8A8 Decode，o_projTP4/denseTP4 |
| ci_950/glm_5_w8a8mxfp8.yaml | 16/16 | npugraph_ex/950 | 1/3 | MXFP8，lmheadTP4，输入截断8192 |

A3另有ci_a3的EP16、CP32+MTP3+offload、EP64样例，均需按实际权重和预算选择。旧pa_block_size/input_max_len/enable_online_split_weight/perfect_eplb字段已不适用；当前分别为scheduler.block_size、data.input_truncated_len、自动权重loader、model.force_eplb。

两份主benchmark YAML当前force_eplb=false，而README性能表说明采集时force EPLB；复现需保留实际覆盖配置，人工均衡不能用于精度验收。当前950配置和A3性能表是不同组合，没有950性能结果可从A3外推。

## 模型限制与启动

attnTP必须1。CP只用于Prefill，由统一metadata按请求切分和恢复，当前整域CP要求world=CP；在线D侧CP1。offload只允许非950、offline且缓存unquant/int8；eager拒绝多流、SuperKernel、cache_compile，npugraph_ex拒绝SuperKernel。moe_chunk_max_len必须正，Prefill块数在EP内对齐后再逐层执行。

从仓根启动，例如：

```bash
bash executor/scripts/infer.sh --model glm_5 --yaml glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml
```

多节点分别执行。模型使用统一Executor，输入可为default或准备好的InfiniteBench。在线P/D使用config/glm_5_pd目录；router据两份world_size定位leader，P主节点上的配置必须与实际角色节点一致。

## 验收与结果

先验证真实权重的合法eager基线，随后单项启用量化、CP、图、多流、投机。检查请求边界、位置、缓存scale与block/slot映射，保存输出、峰值内存、TTFT、Decode执行和端到端时延，区分预热与稳态。950 MXFP8按其FP8缓存、scale布局和算子包单独验收，不能套A3整数参数。

当前A3来源还报告GSM8K96.59%，见[来源观测](../../optimizations/benchmark_observations/glm5_a3_source_benchmark.md)；缺少完整评测和重复资料，不是通用精度保证。本次未执行模型或量化转换。失败时恢复对应权重、合法配置和编译缓存并重验。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/README.md)（primary）
- [modeling_glm.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/modeling_glm.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py)（implementation）
- [weight_convert.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/utils/weight_convert.sh)（implementation）
- [glm_5_w8a8mxfp8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/ci_950/glm_5_w8a8mxfp8.yaml)（implementation）
- [glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_64_64ep_w8a8_prefill_benchmark.yaml)（implementation）
- [glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/config/glm_5_rank_128_128ep_w8a8_decode_benchmark.yaml)（implementation）
