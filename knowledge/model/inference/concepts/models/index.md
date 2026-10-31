# 模型

- [DeepSeek-R1](deepseek_r1.md)：DeepSeek-R1 的 MLA、共享与路由专家及模型结构；部署流程和性能数据分别引用规范入口。
- [DeepSeek-V3.2-Exp](deepseek_v3_2_exp.md)：DeepSeek-V3.2-Exp 的 DSA、MLA 与 Indexer 状态机制；部署、量化和性能各归对应入口。
- [DeepSeek-V4](deepseek_v4.md)：DeepSeek-V4 Flash/Pro 的 Shared-KV、SWA/CSA/HCA、mHC、当前 CacheEntry 生命周期，以及 HiF8、A4W4、DSpark 和 950 低时延 TP 入口。
- [Gemma-4 文本 MoE Decoder](gemma4_26b_a4b.md)：当前Gemma文本Decoder结构、双类型Page cache、FIA v2混合布局、partial RoPE修正与移除local_experts。
- [GLM-5](glm_5.md)：更新GLM-5统一Executor、DSA参数及A3整数/950 MXFP8路径，说明当前CP、Cache与offload边界。
- [GPT-OSS](gpt_oss.md)：当前GPT-OSS的sink/滑窗与clamped GLU、packed/Page cache和独立TP组；部署以BF16、batch1/eager示例验收。
- [HSTU](hstu.md)：HSTU 生成式推荐的离散 ID、jagged 序列、稀疏 Embedding 容量与推荐缓存机制。
- [HunyuanImage-3.0](hunyuan_image_3.md)：当前HunyuanImage的统一YAML、CFG每rank缓存修正、融合布局、A2回退与实际精度/稳态验收边界。
- [HunyuanVideo](hunyuan_video.md)：HunyuanVideo视频DiT、文本编码与VAE结构，统一YAML以及当前缓存、Ring稀疏和950 MXFP8入口。
- [Hy3：GQA、共享专家与当前 PA/MTP 接入](hy3_preview.md)：正式Hy3的当前packed/PA、FP8 QKV融合、SP精确条件、共享专家多流和已接入MTP；纠正旧preview实现。
- [Kimi-K2-Thinking：MLA/MoE 与原生混合精度](kimi_k2_thinking.md)：依据当前Kimi统一Executor实现说明64 heads、原始W4A16/BF16混合精度、packed MLA、CP与MTP边界。
- [LongCat-Flash](longcat_flash.md)：说明 LongCat-Flash 的 ScMoE 双段结构、MLA 与零计算专家；部署流程、优化差异和来源性能分别由 Guide、规则/案例和观测卡维护。
- [LongCat-Flash-Lite](longcat_flash_lite.md)：当前 Lite 双子层、独立N-gram词表、packed/PA缓存、已落地Prefill SP、自动MC2回退与Prolog/多流边界。
- [Qwen3.5-MoE](qwen3_5_moe.md)：当前Qwen3.5混合结构、两组GDN投影、索引Mamba状态、token分片、纯EP/TP与950量化/next_n0边界。
- [Qwen3-MoE](qwen3_moe.md)：当前Qwen3-MoE结构、packed/FP8缓存、950量化、Hadamard与精确Prefill SP触发和实际通信顺序。
- [Qwen3-Next](qwen3_next.md)：Qwen3-Next 是交替使用 Gated Attention 与 Gated DeltaNet、并结合 MoE FFN 的混合注意力模型；模型结构与具体昇腾部署参数分开治理。
- [Qwen Dense (Qwen2 / Qwen3 非 MoE)](qwen_dense.md)：当前Qwen2.5/Qwen3 Dense的GQA与变体差异、packed/PA及新增W8A8融合MLP和scale处理。
- [Sana-Video](sana_video.md)：当前Sana去噪/时序卷积/VAE分工、DP启动、离线文本权重及950混合量化边界。
- [Wan2.2-I2V](wan2_2_i2v.md)：Wan2.2-I2V图文条件、双噪声DiT与VAE，当前CFG默认配置和单卡缓存接入边界。

- [Kimi K3：KDA、Gated MLA、AttnRes 与 LatentMoE](kimi_k3.md)：说明 Kimi K3 混合注意力、沿深度聚合的 AttnRes，以及请求级递推状态与 KV Cache 的区别；部署优化另按 950 实践核对。

- [GLM-5.3-Flash 混合注意力与混合量化](glm_5_3_flash.md)：说明 950DT 适配的34层KDA与11层MLA/DSA、4流mHC、MoE及HiF8/MXFP8/MXFP4的分工和并行边界。
