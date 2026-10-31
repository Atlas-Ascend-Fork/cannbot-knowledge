# 优化案例

保留平台与实现差异，通用条件统一引用对应规则。

- [DeepSeek/Kimi A3 Prefill CP：统一元数据与请求所有者](deepseek_kimi_a3_prefill_cp.md)：按当前统一Executor解释每请求ZigZag、CP整域约束、计算/持久缓存双视图和请求所有者。
- [LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布](longcat_a3_decode_weight_prefetch.md)：当前 LongCat GE/npugraph_ex 的 Decode 预取开关、专用 stream、事件依赖与字节预算边界。
- [LongCat A3 SuperKernel 案例：非 KVP 路径的布局融合修复](longcat_a3_superkernel_layout_fusion.md)：当前 LongCat GE SuperKernel 的分段、后端拒绝条件与布局审查；撤下旧 KVP 分支和跨版本修复示例。
- [LongCat A3 局部 TP 案例：o_proj 与 dense MLP 的 DP/TP 边界](longcat_dp_tp_projections.md)：记录固定 LongCat A3 Decode 在 Attention DP 下的 o_proj K 轴切分、dense MLP 切分和布局转换；沿用局部 TP 规则，不将模型通信序列泛化为统一实现。
- [LongCat-Lite A2/A3 入图案例：NgramEmbedding host gap 与精度边界](longcat_lite_ngram_graph_host_gap.md)：当前N-gram buffer/packed图适配和A2来源对照，撤下旧A3中间值并区分最终Prolog组合结果。
- [变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）](mla_prefill_flash_attention_ntd_layout.md)：变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）。Prefill 里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效率」上此消彼长，选错会浪费算力或撞访存瓶颈。
- [LongCat 多流控核案例（已并入优化规则）](moe_multi_stream_limit_core_num.md)：保留原案例入口；拖尾信号、分核机制、实施风险和证据统一见 Decode 多流控核规则，避免重复维护。原 agnostic 声明不作为跨平台依据，已核验主结论限定 Atlas A3。
- [DSA 长序列 Decode 中 MTP 收益按模块分化的分析案例](mtp_benefit_sparse_attention_and_latency_metric.md)：保留 DeepSeek-V3.2-Exp 在 64K、4 batch 下的 MLA、LI、SFA 搬运量和计算量分析；计时定义统一引用 MTP 计时规则，不将模块分析外推为整网实测加速比。
- [Qwen3-MoE A3 SuperKernel 案例：分段标记与可关闭上下文](qwen3_moe_a3_superkernel_scopes.md)：记录固定 SGLang patch 的 attention/MoE scope、sk_forward 整层入口与 FakeContextManager；关闭分支不等于零开销，整模型数据不能单独归因于 SuperKernel。
- [Qwen3-Next A3 Prefill CP+TP：SGLang 分层并行与 PD 边界](qwen3_next_a3_prefill_cp_tp.md)：固定 Qwen3-Next 实践对 Gated Attention 使用 CP+TP、GDN 保留 TP；记录 SGLang 通信域复用、ZigZag 与 PD 分离限制，区分 README 部署要求和 patch 校验。
- [QSAS 的 HiFloat8 KV 接入案例：按 kv_quant_mode 包装 optional 张量](torchless_lowprec_dtype_acl_override.md)：保留 QSAS 在 kv_quant_mode=10 时把 optional KV 解包为 TensorWrapper、以 ACL_HIFLOAT8 下发的实现差异；通用 dtype 带外传递规则统一引用 AscendC 接口规则，平台能力需另行核对。
- [vLLM MoE 权重预取：token 门控与部分权重比例（平台待核验）](vllm_moe_weight_prefetch_token_gate.md)：固定 vLLM Ascend 实现将专家权重预取接入路由与量化 MLP，按单次 forward token 数门控并使用部分权重比例；平台及具体阶段尚未确认，保留为草稿。
- [HunyuanVideo 950 MXFP8 接入与验证案例](hunyuan_video_950_fp8_quantization.md)：使用当前single_fp8双量化开关，控制CPU offload差异，分别验收单卡/Ulysses量化质量、时延和恢复原权重的回退。
- [Qwen3-Next A3 GDN Context Parallel 案例：ZECO 状态传播与版本限制](qwen3_next_gdn_context_parallel_zeco.md)：记录 PR359 的 GDN CP 实现、单 batch 与 head_dim=128 边界；与早期全注意力 CP 案例分开，不把测量点外推为通用加速规律。
- [HunyuanVideo A3 TaylorSeer offload 案例：导数缓存与搬算流水](video_dit_taylorseer_cache_offload.md)：当前TaylorSeer导数offload流依赖、统一配置和400GB来源提示，撤下无法绑定最新来源的旧估算与性能数。
- [图后端与布局组合的待核验观测：精度、时延和 buffer 配置](graph_backend_layout_unverified_observations.md)：图后端、FIA布局、可变buffer与编译选项的待验证问题；撤下无法绑定原始记录的旧精度和性能断言。
- [V3.2-Exp Offload 的 Prefill 搬运流与事件](deepseek_v32_offload_stream_events.md)：按当前统一缓存和OffloadWorkspace接口说明Prefill事件配对，区分CP持久槽与非CP整层异步复制。
- [A3 Indexer Prolog Decode 多流并行：前处理子链切流](indexer_prolog_streams_fixed_implementation.md)：A3 DeepSeek/GLM 的 Indexer Prolog 在 Decode 将 Q、KV、weights 前处理子链切流，用 GE 控制依赖或 npugraph_ex Stream/Event 同步；核对 overlap、控核、张量生命周期与消费前等待。
- [LongCat A3 AFD 的收发配对与流汇合案例](longcat_a3_afd_stream_pairing.md)：当前 AFD 两半通信组、rank/tag 配对与 npugraph_ex Decode 延迟接收；区分 Prefill chunk 与 Decode 预取。

- [DIA A3 大融合算子的泳道图调优案例](deepseek_indexer_attention_a3_tuning.md)：固定 PyPTO DIA 实现的 Gather、Matmul、barrier 与 reshape 调优，保留75%运行时缩短的来源口径和复测边界。
