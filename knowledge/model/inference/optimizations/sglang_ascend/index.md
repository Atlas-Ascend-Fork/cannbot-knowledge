# SGLang 昇腾量化、并行与模型优化

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang 昇腾 Kimi-K3 的数值守卫与细粒度 shared overlap](sglang_ascend_model_kimi_k3_numerics_overlap.md)：说明 K3 保留 MXFP4 scheme、禁用非等价 QK 融合、latent MoE 空 rank 和 shared expert 流事件依赖。
- [SGLang 昇腾 MiMo V2 的 V scale 向输出权重折叠](sglang_ascend_model_mimo_value_scale_fold.md)：说明加载后对未量化 o_proj 折叠 attention_value_scale、关闭运行时乘法与量化层 fallback。
- [SGLang 昇腾 Qwen3-VL 的 ViT 图与插值一致性](sglang_ascend_model_qwen3_vl_npu_graph.md)：说明 NPU 图入口、精确 attention layout key、CPU 长度及向量化位置插值的模式守卫。
- [SGLang 昇腾 Qwen MoE 的 shared gate 与 DeepEP 双流](sglang_ascend_model_qwen_moe_shared_overlap.md)：说明 shared sigmoid broadcast、图模式中的 NPU overlap、空 rank collective 和缩放责任。
- [SGLang 昇腾 VLM 预处理的八维 reshape 与调度争用](sglang_ascend_model_vlm_preprocess_rank_limit.md)：说明 Qwen、GLM4.6V、MiniMax M3 图像/视频 patch 抽取、Transformers 补丁和 fast processor 设备选择。
- [SGLang 昇腾专家激活的限幅位置与融合守卫](sglang_ascend_moe_activation_fusion.md)：区分 plain SwiGLU、OAI、SiTU 和 swiglu_limit，说明 group_list 语义与激活量化输出。
- [SGLang ascend_ops 的 prefill 与 MC2 decode 通信](sglang_ascend_moe_ascend_ops_communication.md)：说明 AllGather/AllToAllV prefill、MC2 可配置容量 decode、padding 缓冲复用与 combine_quant_mode 的真实值。
- [SGLang 昇腾 EPLB 的地址稳定迁移与 staging 流水](sglang_ascend_moe_eplb_weight_migration.md)：说明 TP=EP=WORLD 前提、参与 rank、非 ND/NZ 临时转换、事件限流和权重先于映射提交。
- [SGLang ascend_fuseep 的通信计算融合与权重模式](sglang_ascend_moe_fuseep_weight_modes.md)：说明 fused_deep_moe 绕过 dispatcher、BF16 通信以及两种权重布局的加载和回退约束。
- [SGLang 昇腾 AWQ 的 nibble 重排与全精度回退](sglang_ascend_quant_awq_repack.md)：说明 AWQ Dense 快路径条件、零点与 nibble 转换、MoE WNA16 适配和回退显存代价。
- [SGLang 昇腾 block FP8 MoE 的默认原生与 opt-in MX 路径](sglang_ascend_quant_block_fp8_moe.md)：说明 BF16 dispatch、原始 FP32 scale、MX 低延迟通信与激活融合守卫之间的关系。
- [SGLang 昇腾 block FP8 转 MXFP8 的无损与有损边界](sglang_ascend_quant_block_fp8_mx_conversion.md)：区分 UE8M0 布局展开和普通 FP32 block scale 的 opt-in 重量化，保留 K 对齐及 DSV4 分组权重约束。
- [SGLang 昇腾 GGUF 的加载反量化与显存预估](sglang_ascend_quant_gguf_dequant_memory.md)：解释 GGUF 在 NPU 上加载到全精度驻留权重、fused shard 顺序和专家隐藏维 all-gather 的代价。
- [SGLang 昇腾原生 G-B block FP8 Dense 路径](sglang_ascend_quant_native_block_fp8_dense.md)：保留 128×128 checkpoint 权重与 FP32 scale，通过原生块量化和 G-B matmul 避免默认 MX 重量化。
- [SGLang 昇腾在线 MXFP4 W4A4 的双层 scale 路径](sglang_ascend_quant_online_mxfp4_dual_level.md)：按实际方法选择区分在线双层 MXFP4 与离线单层 MXFP4，避免沿用过时类注释。
- [SGLang 昇腾在线 MXFP4 W4A8 Dense 与 MoE 回退](sglang_ascend_quant_online_mxfp4_w4a8.md)：说明 950 上在线 FP4 权重与 FP8 激活的真实后端，以及未量化 MoE 回退和 NZ 打包顺序。
- [SGLang 昇腾 W4A8 MoE 的 group scale 与 clip 分支](sglang_ascend_quant_w4a8_group_moe.md)：说明 packed INT4 权重、INT8 激活、per-channel/per-group scale 编码和 activation_use_clip 的补偿参数。
