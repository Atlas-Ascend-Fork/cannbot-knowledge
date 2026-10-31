---
type: Optimization
title: A3 Indexer Prolog Decode 多流并行：前处理子链切流
description: A3 DeepSeek/GLM 的 Indexer Prolog 在 Decode 将 Q、KV、weights 前处理子链切流，用 GE 控制依赖或 npugraph_ex Stream/Event 同步；核对 overlap、控核、张量生命周期与消费前等待。
tags:
- task.optimization
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/stream_utils.py
  role: implementation
created_at: '2026-10-22T01:39:39Z'
updated_at: '2026-10-29T16:00:26Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
---

# Indexer Decode 前处理：GE 与 npugraph_ex 多流

## 当前分支

A3 V3.2-Exp/GLM-5在custom_params.enable_multi_streams且非Prefill时组织Q、Weight、K子链。GE以tagged stream 22/33和npu_wait_tensor连接依赖；npugraph_ex改用模型传入的indexer_prolog/indexer_weight原生NPU流、record_stream及四个torch.npu.Event。旧acl_graph和tagged-event接口已删除，不应作为当前配置。

| 链路 | 工作 | npugraph_ex依赖 |
| --- | --- | --- |
| Q副流 | wq_b→split→RoPE→cat | event0等输入，event1标记wq_b完成，event2标记Q前处理完成 |
| Weight副流 | weights_proj | 等event1，完成记event3 |
| 主流K | wk→LayerNorm→RoPE，必要时量化/写缓存 | int8判断前等event2，消费LI前收口副流结果 |

V3.2-Exp用npu_rotary_mul，GLM-5用npu_interleave_rope。INT8分支Q的Hadamard+dynamic_quant再次进入Q副流，与K量化分开；不能把event2误写为仅INT8分支的同步。所有流共享的张量要保持生命周期，尤其原生流的record_stream。

## 与融合算子的区别

这是indexer.py::prefill_decode_ascendc的多算子链。V3.2-Exp只在enable_pypto且INT8 Cache的Decode分派到独立npu_lightning_indexer_prolog_pto；不能把二者叠成一条已验证执行链。当前代码从显式Indexer Cache参数取数据，slot_mapping/block_table及CP metadata来自统一Executor，不再消费旧runner的past_key_values_indexer列表。

Prefill不启用该多流分支；模型设置检查也拒绝eager+enable_multi_streams。GE和npugraph_ex同步机制按后端选择，不能用“非ACLGraph”概括为eager已验证。

## 验收

保存目标模型、后端、输入及时间线，逐项对齐关闭多流的输出，覆盖INT8/非量化和请求/缓存复用。收益由实际重叠及带宽竞争决定，本来源没有隔离该分流的模块实测增益。概念和融合公式见[Indexer Prolog](../../concepts/kernels/indexer_prolog.md)。


## Evidence

- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（primary）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/modeling_deepseek.py)（implementation）
- [stream_utils.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/utils/stream_utils.py)（implementation）
