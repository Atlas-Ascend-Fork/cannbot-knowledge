# MoE 直调算子

本目录保存专家路由与数据重排类 Direct Invoke 算子知识。

- [MoeFinalizeRouting A5](moe_finalize_routing_a5.md)：MoeFinalizeRouting 算子在 A5 平台的 Direct Invoke 实现，用于恢复专家输出的原始 Token 顺序并合并路由结果。
- [MoeGatingTopKSoftmax A5](moe_gating_top_k_softmax_a5.md)：MoeGatingTopKSoftmax 算子在 A5 平台的 Direct Invoke 实现，用于计算门控概率并选择 TopK 专家。
- [MoeReRouting A5](moe_re_routing_a5.md)：MoeReRouting 算子在 A5 平台的 Direct Invoke 实现，用于按路由结果重排 Token 与专家数据。
