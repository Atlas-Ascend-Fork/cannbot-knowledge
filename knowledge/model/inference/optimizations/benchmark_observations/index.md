# 基准观测

记录来源数据、测量条件和证据缺口，不外推为普遍收益。

- [DeepSeek-V3.2-Exp 当前量化精度来源表](benchmark_deepseek_v32_quant_accuracy.md)：只保留当前提交的量化精度表，明确BF16行原始模型标签及评测环境缺口，移除另一历史版本表。
- [DSA IndexCache 跨层 top-k 复用的 GLM-5 来源观测（平台待核验）](dsa_indexcache_topk_reuse_throughput.md)：GLM-5 W8A8 的来源自报吞吐与精度数据；index_topk_freq 按层控制 top-k 重算，不能解释为跨解码步缓存。卡型及实际 vLLM 依赖版本仍待补。
- [Wan2.2 A2 图模式观测：低 freetime 下暂缓启用](wan22_a2_graph_mode_freetime.md)：记录 Issue 33 对 Wan2.2-I2V/A2 的 720P、480P 单步 freetime 自报及暂不启图的判断；无图模式前后对比，不将百分比当收益保证或通用阈值。

- [DeepSeek-V4 950DT混合量化的来源性能观测](deepseek_v4_950_source_benchmark.md)：更新当前950DT的Flash/Pro完整来源表及HiF8混合方案，保留MTP、强制EPLB和测量缺口。
- [DeepSeek-V4 A3 Pod整数量化的来源性能观测](deepseek_v4_a3_source_benchmark.md)：保留 V4 Flash在A3 Pod的两行Offline Decode自报数据及W8A8C16、MTP1与强制EPLB条件。
- [LongCat A3 AFD与控核的来源性能观测](longcat_a3_afd_source_benchmark.md)：集中固定 LongCat 文档的核数耗时与整网 benchmark；区分可比较配置、perfect EPLB 和测量环境缺口。

- [DeepSeek-R1 A3 Decode 当前来源数据](deepseek_r1_a3_decode_source_benchmark.md)：保留当前README与Decode指南一致的64 Chips性能记录，明确人工路由条件和测量缺口。
- [DeepSeek-R1 A3 Prefill 双流的来源性能观测](deepseek_r1_a3_prefill_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [DeepSeek-V3.2-Exp A3 时延、吞吐与容量的来源观测](deepseek_v32_a3_source_benchmark.md)：集中当前指南仍保留的性能/容量表，区分MTP3/perfect EPLB与实际部署配置，不作性能保证。
- [Gemma-4 A2 当前来源性能与累计阶段](gemma4_a2_source_benchmark.md)：最新Gemma A2累计PA/FIA阶段与GE表分开，撤下已不在当前报告的旧18.21ms值。
- [Gemma-4 A3 当前图后端来源观测](gemma4_a3_source_benchmark.md)：最新Gemma A3 GE/npugraph来源表和吞吐，撤下已删除local_experts配置及不再存在的旧编译表。
- [GLM-5 A3 W8A8 Decode 的来源性能观测](glm5_a3_source_benchmark.md)：集中当前GLM-5 A3性能与新增GSM8K来源观测，明确force_eplb覆盖和评测缺口。
- [HunyuanVideo 950PR 量化的来源性能表](hunyuan_video_950_source_benchmark.md)：当前950PR量化来源表，标明MXFP8实现与offload对照因素，保留单卡/八卡独立baseline。
- [HunyuanVideo A3 累计优化的来源性能观测](hunyuan_video_a3_source_benchmark.md)：最新来源明确默认视频规格与UAA变尺寸，保留A3累计表及非单项归因、测量缺口。
- [HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口](hunyuan_video_sparse_source_observations.md)：最新稀疏与Ring来源表、已接入的当前实现和仍缺失的硬件/build/质量信息。
- [Hy3 A3 基础优化来源记录与当前配置边界](hy3_a3_source_benchmark.md)：最新文档保留的A3基础实验及其与当前npugraph/PA/MTP配置的边界，不混作新配置性能。
- [LongCat-Lite A3 MLA-Prolog 与长输入的来源观测](longcat_lite_a3_prolog_source_benchmark.md)：当前TP报告的A3 5.76ms与4K长输入6.00ms来源结果，区分Prolog实验、稳态和质量边界。
- [LongCat-Lite A3 EP 量化与多流来源观测](longcat_lite_ep_source_observations.md)：最新来源明确A3 EP8下的W8A8与多流/控核结果；更新已解决SP代码缺口，保留测量和质量限制。
- [Qwen3-MoE A3 两条实现的来源时延观测](qwen3_moe_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Sana-Video 950 量化来源观测](sana_video_950_source_benchmark.md)：当前README的480p81f来源结果与测量缺口；不将合并平台表、默认配置或混合位宽误作完整对照。
- [Sana-Video 480p81f 来源时延（平台与精度待核验）](sana_video_bf16_source_observations.md)：当前README的480p81f来源结果与测量缺口；不将合并平台表、默认配置或混合位宽误作完整对照。
- [AutoFuse A3 部分编译与 hc_post 的来源观测](autofuse_a3_source_benchmark.md)：AutoFuse A3 部分编译与 hc_post 的来源观测；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
- [LI/DIA PyPTO 调优的来源观测（测量条件待补）](operator_tuning_source_observations.md)：保留 PyPTO LI 的三项调优披露与 DIA 首版瓶颈比例，目标库支持 A3，但逐次测量环境仍待补。
- [PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）](pypto_v4_operator_source_observations.md)：PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
- [A3 LI TopK 融合与 HcPost 的来源观测](ascendc_a3_li_hcpost_source_observations.md)：分开记录固定 A3 指南的 LI TopK 融合相对收益和 HcPost shape 时延，不将两组测量拼接或外推。

- [Kimi K3 950DT：固定接受长度折算的 Decode 时延观测](kimi_k3_950dt_low_latency.md)：记录 32 卡、100K 输入、256 输出与接受长度按 4 折算下的约 28→10 ms 观测，保留仅统计主草稿模型耗时的边界。
