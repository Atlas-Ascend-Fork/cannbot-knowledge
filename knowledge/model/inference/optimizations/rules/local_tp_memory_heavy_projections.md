---
type: Optimization
title: 局部 TP：检查权重切分及 DP→TP→DP 边界
description: 更新统一o_proj_tp_size及当前分片loader偏移、局部Embedding初始化，核对局部TP的通信和内存收益。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k2_thinking/kimi_k2_thinking_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T14:58:30Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - decode
      objective:
      - memory
      - latency
      - tpot
      model_features:
        all_of:
        - moe
      parallelism:
        all_of:
        - dp
        - ep
---

# 局部 TP：检查权重切分及 DP→TP→DP 边界

当前A3 MoE Decode实践在Attention DP、MoE EP之外，对o_proj、dense MLP、LM Head、Embedding分别做局部TP，以减少复制权重与搬运；要同时计入布局转换通信，不因模型用了MoE就统一增加TP。

| 目标 | 必须核对 | 验收 |
| --- | --- | --- |
| o_proj | 输入K轴分片、head输出顺序、模型的AllToAll/AG/RS路径 | 投影及转换通信时间、输出 |
| dense MLP | gate/up输出分片、down输入分片、token恢复 | 中间显存、padding、通信 |
| LM Head/Embedding | vocab分片、加载rank偏移、logits或查表合并 | 加载峰值、token/logits一致 |

当前统一InferenceConfig里Kimi、LongCat都使用o_proj_tp_size，旧Kimi oproj_tp_size字段不再适用；删去的LongCat model_setting.py也不是配置入口。校验与前向都应按当前模型读取：Attention-DP讨论的attnTP1不等于所有模型都禁止attnTP与o_projTP共同启用。具体LongCat切分见[模型案例](../cases/longcat_dp_tp_projections.md)。

module/linear.py当前Column/MergedColumn按N切、Row按K切；后两者可接shard_full_size/shard_offset表示非均匀分片的加载起点，不能一律用tp_rank×shard_size。VocabParallelEmbedding直接分配局部词表，padding_idx按rank归属转换成局部下标。减少初始化内存不等于运行时延收益。

Kimi文档建议TP通信尽量留在节点内，迁移须核对真实拓扑，不能直接等同固定TP数。旧Issue的OOM建议不构成当前可复用配方；先区分权重、KV、临时激活、通信buffer与batch整除问题。

固定权重、输入/输出长度、batch、量化及其余开关，比较峰值显存、投影/通信、Decode/TPOT并验输出。通信抵消收益或布局不一致时恢复原合法配置，重新核对缓存与通信组。本次没有NPU复测。

## Evidence

- [kimi_k2_thinking_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/kimi_k2_thinking/kimi_k2_thinking_inference_guide.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/kimi_k2_thinking/models/modeling_deepseek.py)（implementation）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
- [linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)（implementation）
- [inference_config.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/config/inference_config.py)（implementation）
