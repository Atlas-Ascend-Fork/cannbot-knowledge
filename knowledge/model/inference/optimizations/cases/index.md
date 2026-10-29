# 优化案例

保留平台与实现差异，通用条件统一引用对应规则。

- [DeepSeek/Kimi A3 Prefill CP：整域约束与阶段门控](deepseek_kimi_a3_prefill_cp.md)：记录两个固定 cann_executor 实现的 cp_size 等于 world_size 校验、ZigZag 与 KV 汇聚；DSA 细节和 Kimi 部署规模分别说明，不推广到 SGLang。
- [LongCat A3 Decode 权重预取：QBMM 与 MLA_Prolog 的相邻排布](longcat_a3_decode_weight_prefetch.md)：记录固定 LongCat-Flash/A3 实现中的预取空间取舍、enable_prefetch 开关和验证边界；不提供独立控变量收益，也不继承 vLLM 的 token 门控或比例。
- [LongCat A3 SuperKernel 案例：非 KVP 路径的布局融合修复](longcat_a3_superkernel_layout_fusion.md)：记录 PR332 将 reshape 下沉分支、恢复 bmm 与 transpose 相邻性的固定修复；不将历史 KVP 分支当作当前能力，也不保证所有算子均可融合。
- [LongCat A3 局部 TP 案例：o_proj 与 dense MLP 的 DP/TP 边界](longcat_dp_tp_projections.md)：记录固定 LongCat A3 Decode 在 Attention DP 下的 o_proj K 轴切分、dense MLP 切分和布局转换；沿用局部 TP 规则，不将模型通信序列泛化为统一实现。
- [LongCat-Lite A2/A3 入图案例：NgramEmbedding host gap 与精度边界](longcat_lite_ngram_graph_host_gap.md)：记录固定报告的 NgramEmbedding 图外时间和 GE 入图收益，区分 A2/A3 数据、稳态条件与 token 分歧；报告的语义等价判断不作为本次精度验收。
- [变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）](mla_prefill_flash_attention_ntd_layout.md)：变长 Prefill 的 MLA FlashAttention 布局选 NTD（免 padding 又避 TND 的转置 / 带宽损失）。Prefill 里请求 seq_len 不定长（每请求长度不同），MLA 段的 FlashAttention 要选输入布局。三种候选在「免 padding」与「访存 / 转置效…
- [LongCat 多流控核案例（已并入优化规则）（已停用）](moe_multi_stream_limit_core_num.md)：保留原案例入口；拖尾信号、分核机制、实施风险和证据统一见 Decode 多流控核规则，避免重复维护。原 agnostic 声明不作为跨平台依据，已核验主结论限定 Atlas A3。
- [DSA 长序列 Decode 中 MTP 收益按模块分化的分析案例](mtp_benefit_sparse_attention_and_latency_metric.md)：保留 DeepSeek-V3.2-Exp 在 64K、4 batch 下的 MLA、LI、SFA 搬运量和计算量分析；计时定义统一引用 MTP 计时规则，不将模块分析外推为整网实测加速比。
- [Qwen3-MoE A3 SuperKernel 案例：分段标记与可关闭上下文](qwen3_moe_a3_superkernel_scopes.md)：记录固定 SGLang patch 的 attention/MoE scope、sk_forward 整层入口与 FakeContextManager；关闭分支不等于零开销，整模型数据不能单独归因于 SuperKernel。
- [Qwen3-Next A3 Prefill CP+TP：SGLang 分层并行与 PD 边界](qwen3_next_a3_prefill_cp_tp.md)：固定 Qwen3-Next 实践对 Gated Attention 使用 CP+TP、GDN 保留 TP；记录 SGLang 通信域复用、ZigZag 与 PD 分离限制，区分 README 部署要求和 patch 校验。
- [QSAS 的 HiFloat8 KV 接入案例：按 kv_quant_mode 包装 optional 张量](torchless_lowprec_dtype_acl_override.md)：保留 QSAS 在 kv_quant_mode=10 时把 optional KV 解包为 TensorWrapper、以 ACL_HIFLOAT8 下发的实现差异；通用 dtype 带外传递规则统一引用 AscendC 接口规则，平台能力需另行核对。
- [vLLM MoE 权重预取：token 门控与部分权重比例（平台待核验）](vllm_moe_weight_prefetch_token_gate.md)：固定 vLLM Ascend 实现将专家权重预取接入路由与量化 MLP，按单次 forward token 数门控并使用部分权重比例；平台及具体阶段尚未确认，保留为草稿。
- [HunyuanVideo 950 FP8 量化接入与验证案例](hunyuan_video_950_fp8_quantization.md)：保留单卡/Ulysses8的量化接入与质量边界，完整性能数字统一引用平台观测。
- [Qwen3-Next A3 GDN Context Parallel 案例：ZECO 状态传播与版本限制](qwen3_next_gdn_context_parallel_zeco.md)：记录 PR359 的 GDN CP 实现、单 batch 与 head_dim=128 边界；与早期全注意力 CP 案例分开，不把测量点外推为通用加速规律。
- [HunyuanVideo A3 TaylorSeer offload 案例：导数缓存与搬算流水](video_dit_taylorseer_cache_offload.md)：记录 720p 129 帧的主机内存门槛、预取流水及来源自报观测；区分 PR266 的单卡限制与 PR356 新增的 SP8 配置。
- [图后端与布局组合的待核验观测：精度、时延和 buffer 配置](graph_backend_layout_unverified_observations.md)：从旧图模式 Concept 迁出并保留来源不明的兼容性表、性能数值和配置；平台、环境及原始记录待补，不作为通用部署建议。
- [V3.2-Exp KV Offload 搬运流与事件配对案例](deepseek_v32_offload_stream_events.md)：V3.2-Exp KV Offload 搬运流与事件配对案例，保留固定实现条件与观测边界，未独立复测。
- [A3 Indexer Prolog Decode 多流并行：前处理子链切流](indexer_prolog_streams_fixed_implementation.md)：DeepSeek/GLM 的 Decode 前处理把 Q、Weight、K 子链分到不同流，按 GE/acl_graph 后端同步以争取计算重叠；固定 A3 源码支持该实现，不含模块级控核配比或实测收益。
- [LongCat A3 AFD 的收发配对与流汇合案例](longcat_a3_afd_stream_pairing.md)：LongCat A3 AFD 的收发配对与流汇合案例；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
