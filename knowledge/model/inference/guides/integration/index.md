# 模型集成指南

组合能力的接口适配、验证与回退。

- [块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）](blockwise_sparse_attention_ulysses_integration.md)：块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）。长序列视频 DiT 想同时吃到两种降本：块稀疏 Attention（TopK/SVG 丢弃低注意力块）减计算量，Ulysses 序列并行摊显存/时延。两者天然冲突，直接叠加会算错，须解决三处问题…
- [把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写](graph_break_elimination_host_sync_unsupported_ops.md)：把 decode 逻辑塞进图前消除 graph break：host 同步 / host 构造张量 / 图后端不支持算子的图安全改写。要把一段 decode 逻辑整图编译进 GE 图 / aclgraph（npu-graph-mode），但它含 host 依赖或图后端不支持的算子，捕获失败 / 断图 / 走 CPU fallback。上图前先按下面几类逐条排查、把图中断（graph break）改成图安全等价——这是把 decode 从 eager 迁到图模式的核心适配工作。是否值得为某模块付这份适配见 graph-mode-enable-decision-profiling。
- [MTP 接入：共享权重、隐状态与惰性注册](mtp_speculative_decode_model_onboarding.md)：新模型接入 MTP 推测解码：draft 构造、主草稿权重共享、prev_hidden_states、惰性注册、packed 输入与贪心 verify；旧三元组注册应迁移到当前模型对。
- [SFA/DSA 稀疏注意力叠加 Context Parallel：跨 CP 组重建完整 KV 的 all_gather 路径](sfa_dsa_cp_cross_group_kv_allgather.md)：固定 vLLM Ascend SFA/DSA + PCP/DCP 集成路径：选择有效 block，依次 DCP→PCP all_gather，并对齐 CP KV 交错粒度；该版本 PCP Prefill 不支持 MLAPO。A3 配置与数据流已有源码依据；PR 精度数字的平台仍未知。
