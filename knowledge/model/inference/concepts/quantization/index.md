# 量化

- [MXFP8 量化注意力（HunyuanVideo）](fp8_attention.md)：说明当前HunyuanVideo的TND动态MXFP8注意力：Q/K沿hidden维采用mode6，V沿序列轴采用mode8，限定纯Ulysses、950及CANN9.1+并保留错误定位边界。
- [DeepSeek-V4 950 混合量化：HiF8、MXFP8 与 MXFP4](hybrid_mxfp8_mxfp4.md)：更新 950 的 HiF8 混合矩阵、FP8/HiF8 KV 记录格式和 A4W4 的转换、路由及加载校验。
- [Int8 / Hybrid INT8-INT4 (DeepSeek-V4 Atlas A3 Pod)](int8_int4_hybrid.md)：V4 A3 的 W8A8C16 与路由专家 W4A8、共享专家 W8A8 的混合矩阵；更新转换选项并保留当前 GMM bias。
- [MXFP8 A8W8 (DiT Linear)](mxfp8_a8w8.md)：HunyuanVideo 针对 DiT 中 Linear 层（MLP / 投影层）的 Micro-scaling FP8 矩阵量化方案：权重按 group（默认 `group_size=32`）per-group 量化为 FP8 E4M3FN，激活按 token 维度 per-token 量化为同格式，scale 采用 E8M0（纯指数，1 字节）。实现 8-bit × 8-bit 矩阵乘（A8W8），BF16 权重数据本体由每元素 2 字节降为 1 字节（未计 scale）；这一理论数据比例和来源所称权重加载带宽降低 50%，均不代表包含激活、scale、未量化层的整体带宽需求减半。调用 `torch_npu.npu_dynamic_mx_quant` + `torch_npu.npu_quant_matmul` 完成量化与量化 GEMM。
- [W4A8C8 (MoE W4A8 + Attention W8A8C8)](w4a8c8.md)：DeepSeek-V3.2-Exp 的 W4A8C8 在 MoE 路由专家使用 4-bit 权重，其余模块沿用 W8A8C8；本卡解释逐模块精度和 Clamp 边界，性能与精度数据分别引用观测。
- [W8A8C8](w8a8c8.md)：解释 W8、A8、C8 在不同模型中的模块覆盖、粒度与 scale 链路；精度和性能按独立来源观测验收。
