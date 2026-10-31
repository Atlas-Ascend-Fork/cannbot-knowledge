---
type: Optimization
title: 跨 Prefill/Decode 的集群配置核对：区分 rank、阶段与验证范围
description: 核对跨 Prefill/Decode 的默认 config 集群规模、world_size、rank、物理卡数与 batch 差异；非默认卡数需按模型校验和真实验证范围调整。
tags:
- task.optimization
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T16:00:26Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      - decode
      objective:
      - bringup
---

# 分别核对 Prefill 与 Decode 的集群配置

当前DeepSeek-V3.2-Exp两份benchmark YAML仍按不同规模配置：

| 样例 | world_size | batch_size | cp_size | dense_tp_size |
| --- | ---: | ---: | ---: | ---: |
| rank_64_64ep_prefill_benchmark | 64 | 64 | 64 | 1 |
| rank_128_128ep_decode_benchmark | 128 | 256 | 128 | 4 |

两份当前均next_n=1、attn_tp_size=1、o_proj_tp_size=8、moe_tp_size=1、block_size=128，使用统一Executor。YAML注释按A3 world_size=2×chip_num换算，不能把rank数直接当所有硬件的物理卡数。

CP仅Prefill生效；离线Decode配置写cp_size=128不证明Decode进行了序列切分。在线PD的DecodeScheduler则明确要求CP=1，不能把离线benchmark YAML原样作为在线Decode配置。

迁移逐项核对本实例rank/设备数、TP/EP/CP组、batch/请求所有者、缓存布局及Prefill预算，再按目标负载验证输出、峰值显存、TTFT和Decode耗时。样例batch只说明配置值，不是硬件容量上限；旧Issue自报的已测规模也不能替代当前版本实测。本次未运行模型。

参见[长序列CP](long_seq_prefill_context_parallel.md)和[在线PD](../../concepts/frameworks/online_pd_inference.md)。


## Evidence

- [deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml)（primary）
- [deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/config/deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（implementation）
- [decode.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/online/scheduler/decode.py)（implementation）
