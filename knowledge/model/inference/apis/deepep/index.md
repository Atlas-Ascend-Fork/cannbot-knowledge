# DeepEP 通信接口

- [DeepEP fused_deep_moe：融合模式、激活与返回计数差异](deepep_fused_deep_moe.md)：说明 FUSED_DEEP_MOE、DISPATCH_FFN_COMBINE、MEGA_MOE 的公开分发边界，限定 A3 与950的激活、权重契约和第二返回值语义。
- [DeepEP get_dispatch_layout：Normal 路由统计与返回值边界](deepep_get_dispatch_layout.md)：整理 Normal dispatch 前的专家与 rank 计数、输入连续性和分整除要求，区分文档预留的 RDMA/事件字段与不同 Python 策略的实际行为。
- [DeepEP Low-Latency：容量、有效 token 与量化兼容边界](deepep_low_latency_dispatch_combine.md)：整理 Decode 分发/聚合的固定容量、专家有效计数和 handle 配对，区分 default、ops、alltoall 的 padding、量化与事件行为。
- [DeepEP MegaMoe：量化映射、权重布局与对称缓冲生命周期](deepep_mega_moe.md)：限定 CANN9.2.0 MegaMoe 在A3的padding/active mask与950的实际token长度，说明MXFP TensorList布局、缓存key和资源销毁。
- [DeepEP Normal dispatch/combine：配套句柄、量化选择与策略差异](deepep_normal_dispatch_combine.md)：定义 Normal token 分发与聚合的数据/scale 契约，记录公开 dispatch 没有 quant_mode 形参、量化标志互斥及 alltoall 与 default 的差异。
