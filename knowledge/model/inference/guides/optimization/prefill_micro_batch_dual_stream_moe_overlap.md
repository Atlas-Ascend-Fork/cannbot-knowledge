---
type: Guide
title: R1 Prefill 微批双流：按请求切分并对齐通信轮次
description: 更新当前R1按请求边界切packed微批、两种双流流水及EP一致chunk轮次，明确开关和验收。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/utils.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:57:06Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - throughput
---

# R1 Prefill 微批双流：按请求切分并对齐通信轮次

## 条件与开关

当前R1在custom_params.micro_batch_mode中选择0关闭、1 DP+EP、2 SP-TP-EP。它独立于enable_multi_streams，后者不能关闭本Prefill流水。mode1要求attn_tp_size=1且moe_tp_size=1；至少两个请求，单个长请求不会自动切成两份，少于两个直接RuntimeError。

当前prefill_r1_rank_32_32dp_32ep_a8w8.yaml为world32、batch64、输入截断4096、max_new_tokens10，mode1，使用统一Executor。图配置ge_graph仅作用Decode，Prefill双流本身仍eager。

## Packed 输入和切分

1. gen_microbatch_input要求position_ids，读取每请求真实seq_lens，按累计token接近一半的位置选请求边界，并限制两边非空。
2. build_microbatch_inputs依据边界切input_ids、position_ids和每类slot_mapping；两份各自重算累计Q/KV长度。校验总请求数和token数守恒，不能按旧固定BSND形状拆view。
3. SP模式可补齐至attnTP整除，local_output_tokens与实际request_count分开，LM Head前仍按真实请求边界恢复。

## 流水

mode1的MoE层拆成Attention、init-routing、dispatch、expert、combine、finalize六阶段；计算在主流，AllToAll在stream1，通过record/wait事件让不同微批的通信与计算交错。前置Dense层走独立分支，不能给它套同一六段。

mode2把mb0/mb1的Attention和MLP分别放两流，并非固定“主流计算、副流通信”。当前每个微批在进入层循环前单独求EP一致的MoE chunk数；get_moe_num_chunks对本地分块数做EP MAX，split_moe_tensors用tensor_split返回确切份数，含空片，保证变长rank执行相同轮次集合通信。不能在每层重新同步，也不能因本地无token跳过全组通信轮。

两模式收尾均双向wait_stream后归一化/拼接；逐事件顺序以当前函数为准，不能用Decode indexed Event或旧acl_graph tagged-event代码替代。

## 性能前提与验收

切小shape后计算/通信效率需保持，且原负载有可掩盖的通信空洞；Host瓶颈时双流增加下发可能变慢。来源建议本Prefill流水用默认SDMA，避免HCCL_OP_EXPANSION_MODE=AIV抢Vector；这不等于所有Decode场景都禁AIV。

先保存mode0输出/时间线，再覆盖不等长、最少两个请求、SP补齐、不同rank token量与MTP。核对无请求/token丢失、KV槽一致和集合通信次数，记录稳态吞吐、TTFT与峰值内存。数字见[R1 Prefill来源观测](../../optimizations/benchmark_observations/deepseek_r1_a3_prefill_source_benchmark.md)，本次未执行模型。无净收益或不对齐时micro_batch_mode=0回退并重验。


## Evidence

- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py)（primary）
- [utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/utils.py)（implementation）
- [prefill_r1_rank_32_32dp_32ep_a8w8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/config/prefill_r1_rank_32_32dp_32ep_a8w8.yaml)（implementation）
- [deepseek_r1_prefill_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_r1/deepseek_r1_prefill_optimization.md)（implementation）
