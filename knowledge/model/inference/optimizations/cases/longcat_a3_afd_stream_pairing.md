---
type: Optimization
title: LongCat A3 AFD 的收发配对与流汇合案例
description: 当前 AFD 两半通信组、rank/tag 配对与 npugraph_ex Decode 延迟接收；区分 Prefill chunk 与 Decode 预取。
tags:
- task.optimization
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md
  role: supporting
created_at: '2026-10-22T01:37:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
      deployment_topology:
        all_of:
        - afd
---

# LongCat A3 AFD 的 rank 配对与汇合

## 拓扑与标签

world_size 为偶数，前半 FFN、后半 Attention。Attention rank R 与 R-world/2 配对；FFN 反向加 world/2。Attention send_tag=layer_idx、recv_tag=layer_idx+num_hidden_layers，与 FFN 对应互换。当前按两半分别建立业务通信组，各组大小须整除 half-world，所有 rank 共同注册相同 subgroup 分区。

## 当前收发顺序

Attention 先计算第一段 attention/norm，再 send hidden_states_norm；本地继续 dense MLP 与第二段 attention。npugraph_ex Decode 将 recv 延迟到相加前；其他路径在发送后接收。不能保留旧“所有分支 send 后立刻 recv”的示例，也不能仅凭 Python 调用顺序断言设备通信完全重叠。

FFN 侧 recv→router→dispatch/GMM/combine→send。Prefill 使用全局一致 chunk 的 double routing，Decode 使用 dispatch/combine，并可返回 gmm2_event 支持下一层预取。

## 验证与失败信号

按[AFD 规则](../rules/afd_attn_ffn_disaggregation.md)检查两半数量、rank/tag、通信组与图后端。记录 Attention 接收等待和 FFN 热点，区分配对错误、网络问题与计算拖尾。预取优化见[FFN 诊断](../../runbooks/performance/afd_ffn_side_bottleneck_prefetch.md)。本次未执行分布式推理；源码存在延迟接收不证明收益。


## Evidence

- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（primary）
- [ffn.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/ffn.py)（implementation）
- [longcat_flash_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/longcat_flash/longcat_flash_optimization.md)（supporting）
