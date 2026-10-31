# 概念

- [框架](frameworks/index.md)：共 12 张知识卡（如 GraphTrainer：联合训练图中的通信与计算调度、MindSpeed-Bridge（运行时注册与 HF/Megatron 权重映射）、MindSpeed（昇腾大模型训练加速框架 + 低精度训练） 等）。
- [融合 Kernel](kernels/index.md)：共 9 张知识卡（如 GDN Chunk 算子（solve_tril / chunk_delta_h / chunk_o / wy_fast Triton 核）、MHC 训练（融合 Pre/Post 与 Triton Head）、SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子） 等）。
- [网络模块](modules/index.md)：共 6 张知识卡（如 DeepSeek-V3.2 / V4 MTP 训练（串联预测与损失）、Engram 训练：Host 记忆表、稀疏更新与联合分片、Gated DeltaNet 训练（Chunk 并行 / Flash 递归 / GDN 上下文并行） 等）。
- [并行策略](parallelism/index.md)：共 8 张知识卡（如 MindSpeed 上下文并行家族（Ulysses / Ring / Hybrid / Unaligned CP）、DSA 上下文并行（TND 与压缩 KV 布局）、DualPipeV（V 形双向流水 + Zero-Bubble dw 分离） 等）。
- [量化](quantization/index.md)：HiF8 编码、缩放和来源报告的低精度训练收益；当前 TorchAO-NPU all_hif8、V4 LI HiFloat8 与 FSDP 预量化边界。
- [优化技术](techniques/index.md)：共 35 张知识卡（如 Agent RL 执行范式（asyncLLM 异步生成 + agent_loop 多轮工具调用）、Auto-Settings（并行/重计算/内存配置自动搜索）、训练入图：torch.compile + Inductor + AutoFuse（Bypass Triton → AutoFuse） 等）。
