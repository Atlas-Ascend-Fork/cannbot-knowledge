# 并行策略

- [CFG Parallel](cfg_parallel.md)：CFG独立分支通信与质量/成本边界，当前Wan默认CFG2×Ulysses4且多卡禁用缓存。
- [Data Parallel](data_parallel.md)：将不同的请求/batch 分配到不同的模型副本上并行推理的策略，用于提升推理吞吐量。在推理场景中通常以 DP 通信域的形式与 TP/EP 配合使用。
- [Embedding Tensor Parallel](embedding_tp.md)：Embedding Tensor Parallel（Embedding TP）是针对**稀疏参数占主导**的推荐/生成式推荐模型的并行策略：把超大规模的 **Embedding Tables 按 vocab 维度切分**到多张 NPU 上，以减少单卡显存负担，支撑超大 Embedding 词表的推理。在 cann-recipes-infer 中首次用于 hstu（Meta 生成式推荐模型）。 与 LLM 的 tensor-parallel 切 Attention Head / FFN 隐藏维度不同：LLM 参数主要集中在 dense Transformer 权重里，输入 token 来自相对固定的文本词表；而**生成式推荐往往把用户、物品、上下文等离散特征统一建模为 token，模型容量绝大部分来自超大规模的稀疏参数（Embedding Tables），词表规模可达千万甚至上亿**。
- [KVP（KV Parallelism）：长序列 Decode 的 KV Cache 序列分片与历史状态](kvp.md)：当前版本不提供 LongCat KVP 配置或部署入口；撤下旧代码、旧 YAML 和多提交历史配方。
- [Ring Attention Sequence Parallelism](ring_attention.md)：Ring概念与当前AllGather实现、两路LSE、Hybrid及MXFP8/UAA/块稀疏组合边界。
- [SP-TP-SP Hybrid Split (Prefill MLA)](sp_tp_sp.md)：DeepSeek-R1 Prefill 阶段 MLA 部分针对 DP 切分在短序列混合/请求数少场景下 **计算负载不均 + TTFT 被拉长** 问题提出的混合切分策略：把 batch 与 seq_len 合轴变为 token 数，按卡数 **SP** 切 token 均匀分发；FlashAttention 计算走 **TP** 切 head；FA 结束后 AllToAll 再转回 **SP** 给 o_proj。"SP → TP（FA）→ SP" 三段式得名。
- [Tensor Parallel](tensor_parallel.md)：将模型权重沿 Head 或隐藏维度切分到多张卡上并行计算的策略，是 NPU 推理中最基础的并行方式。具体使用模块与阶段由模型实现决定，也可与 DP/EP 配合。
- [Ulysses Sequence Parallelism](ulysses.md)：Ulysses序列/head交换、UAA填充边界、纯Ulysses限制和当前块稀疏接入。
- [VAE Patch Parallel](vae_patch_parallel.md)：VAE 编解码的空间并行：HunyuanImage-3.0 与 Wan2.2-I2V 使用 H/W 网格及按算子选择的通信；HunyuanVideo 使用沿宽度的 overlap-chunk decode。说明平台实现、切分范围与边界处理。
- [ZigZag Context Parallel (Load-Balanced Causal Attention)](zigzag_cp.md)：ZigZag 是 context-parallel 下针对**因果 Attention 负载不均**的切分变体：将输入 Sequence 切成 `2·cp_size` 个 block，每个 CP rank 负责头尾对称的两个 block（如 rank 0 负责 block 0 与 block 2·cp_size-1），从而让所有 rank 的历史 KV 计算量近似相等。通过两次 AllToAll 在"因果序"和"ZigZag 序"之间切换。 定位：ZigZag 是 CP 的**并行切分策略**（不是正交的通用技术），放在 parallelism 目录下；与 Ulysses/Ring Attention SP 并列作为长序列并行的一个方案族。

- [上下文并行（Context Parallel / CP）：长上下文 Prefill 的序列切分](context_parallel.md)：CP 沿 Sequence 维度切分长上下文 Prefill 的计算，降低单 Rank 的激活值压力。区分 Qwen3-Next 的 CP+TP 与其他整域 CP 实现；通信域、KV 汇聚及 PD 分离限制按具体案例核对。
- [MoE 专家并行（Expert Parallel / EP）：Prefill 与 Decode 的专家切分和通信](expert_parallel.md)：EP 将 MoE 专家分布到多个 Rank，通过 dispatch/combine 分发和收回 token；不以 MLA 为前提，Attention 结构及其 TP/DP 是独立维度。说明 Prefill、Decode 的已知部署方案及与 TP 的分工；吞吐和时延仍取决于负载均衡、通信与具体实现，不能仅由启用 EP 推定收益。
