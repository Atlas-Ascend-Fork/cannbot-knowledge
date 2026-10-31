# 网络模块

- [Blockwise Sparse Attention (TopK / SVG)](blockwise_sparse_attention.md)：当前块稀疏TopK/SVG、离线CAC、Ulysses负载均衡和已接入Ring/LSE，说明SVG overlap回退及缓存互斥。
- [Diffusion Transformer (DiT)](dit.md)：DiT视频生成的去噪、文本/VAE与guidance职责，当前MXFP8、稀疏metadata和各模型缓存/并行接入边界。
- [DSA（DeepSeek Sparse Attention）架构模式](dsa.md)：DSA 的 MLA 与学习式 Indexer 关系；区分教学 mask 与实际稀疏算子，并更新 GLM-5 FP8 和 V4 Shared-KV 的例外。
- [Gated Attention](gated_attention.md)：门控Attention机制与当前3.5 Page cache/分片归约/950量化边界，区分Next投机与C8实现。
- [Gated DeltaNet (GDN)](gated_deltanet.md)：当前GDN递推机制、Next自研与Qwen3.5原生差异、两组投影/索引Mamba状态及已删除chunk回退。
- [Lightning Indexer (LI)](lightning_indexer.md)：LI 的加权 ReLU 打分与精确 TopK 模块，区分 V3.2 packed 缓存和 V4 压缩缓存及 HiF8/FP8/Int8 分支。
- [mHC (Manifold-Constrained Hyper-Connections)](mhc.md)：mHC（Manifold-Constrained Hyper-Connections，arXiv 2512.24880）是 DeepSeek-V4 引入的传统残差连接扩展，与 Attention、MoE 并列为每个 Layer 的三模块之一。核心：把层间 hidden 从单路残差扩展为多路残差（路数 `hc_mult`；Native 参考实现签名默认 4，实际生产取权重 config，仓内无硬编码全局默认），用 Pre / Post / Res(comb) 三类可学习映射在多路↔单路间转换——每个子层（Attention 一次、MoE 一次）经 `HcPre` 把多路融合回一路（RMSNorm + linear(hc_fn) + pre 加权求和）送入子层，子层一路输出经 `HcPost` 用 Post 系数（`2·sigmoid`）扩展回多路并与 Res(comb) 混合后的多路残差加和。Res(comb) 混合矩阵经 **Sinkhorn-Knopp 迭代**（softmax→列归一→`iters-1` 轮行列交替归一）约束逼近双随机矩阵（论文'流形约束'）。本页讲结构语义与计算公式（以 `mhc.py` 代码为准）；`HcPre`/`HcPost` 融合算子的 A3 分离架构 CV 流水/Tiling/性能为独立子主题。
- [MLA (Multi-head Latent Attention)](mla.md)：DeepSeek-V3 系列（DeepSeek-R1、Kimi-K2）使用的低秩压缩注意力机制。通过将 Q 和 KV 分别投影到低维隐空间（`q_lora_rank`、`kv_lora_rank`）再上投到 full rank，实现 KVCache 体积的显著压缩；RoPE 仅作用于一个较小的 `qk_rope_head_dim` 通道，与 NoPE 通道拼接。相较标准 MHA，MLA 在同样上下文长度下 KVCache 占用显著更小，推理时通过融合算子 mla-prolog 将 Q/K/V Linear + LayerNorm + RoPE + KVCache 写入整体合并，进一步降低下发开销。 训练侧（MindSpeed-LLM CustomMLASelfAttention）默认 mla_naive_attention 走完整 q/kv 上投影 + RoPE + FlashAttention、无 decode KV-cache absorption；--enable-mla-absorb 仅稀疏注意力下吸收 W_UK/W_UV 压激活显存；经 features_manager 的 MLAFeature/DSAIndexerFeature/G2Feature 注册，配合 TP/SP/CP 与 mla-zero-memory 等重计算。
- [Sparse Flash Attention (SFA)](sparse_flash_attention.md)：DSA 中选定 TopK 后的稀疏注意力，更新 packed 索引、C8 Query 拼接与返回值，保留 Absorb/CP 的模型边界。
- [VAE（多模态生成）](vae.md)：VAE 在生成模型中完成像素与 latent 之间的编解码；图像条件推理也会调用 Encoder。涵盖按模型区分的 VAE 并行、mask 缓存和 offload 调整，并区分 VAE 与去噪网络优化。
