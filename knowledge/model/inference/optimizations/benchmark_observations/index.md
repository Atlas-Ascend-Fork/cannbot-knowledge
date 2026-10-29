# 基准观测

记录来源数据、测量条件和证据缺口，不外推为普遍收益。

- [DeepSeek-V3.2-Exp 三档量化精度的来源观测与评测缺口](benchmark_deepseek_v32_quant_accuracy.md)：记录 W8A8C16、W8A8C8、W4A8C8 的两版来源自报精度表；各自对照对应 BF16 基线，保留平台、评测命令与重复测量缺口，不据此制定跨模型验收阈值。
- [DSA IndexCache 跨层 top-k 复用的 GLM-5 来源观测（平台待核验）](dsa_indexcache_topk_reuse_throughput.md)：GLM-5 W8A8 的来源自报吞吐与精度数据；index_topk_freq 按层控制 top-k 重算，不能解释为跨解码步缓存。卡型及实际 vLLM 依赖版本仍待补。
- [Wan2.2 A2 图模式观测：低 freetime 下暂缓启用](wan22_a2_graph_mode_freetime.md)：记录 Issue 33 对 Wan2.2-I2V/A2 的 720P、480P 单步 freetime 自报及暂不启图的判断；无图模式前后对比，不将百分比当收益保证或通用阈值。

- [DeepSeek-V4 950DT混合量化的来源性能观测](deepseek_v4_950_source_benchmark.md)：集中 V4 总览与量化卡已引用的 950DT 数据，补齐 GBS，保留 MTP、强制 EPLB 和统计缺口。
- [DeepSeek-V4 A3 Pod整数量化的来源性能观测](deepseek_v4_a3_source_benchmark.md)：保留 V4 Flash在A3 Pod的两行Offline Decode自报数据及W8A8C16、MTP1与强制EPLB条件。
- [LongCat A3 AFD与控核的来源性能观测](longcat_a3_afd_source_benchmark.md)：集中固定 LongCat 文档的核数耗时与整网 benchmark；区分可比较配置、perfect EPLB 和测量环境缺口。

- [DeepSeek-R1 A3 Decode 的来源数据与 Chips 分歧](deepseek_r1_a3_decode_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [DeepSeek-R1 A3 Prefill 双流的来源性能观测](deepseek_r1_a3_prefill_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [DeepSeek-V3.2-Exp A3 时延、吞吐与容量的来源观测](deepseek_v32_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Gemma-4 A2 图模式的两组来源性能口径](gemma4_a2_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Gemma-4 A3 图后端与 EP 路由的来源观测](gemma4_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [GLM-5 A3 W8A8 Decode 的来源性能观测](glm5_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [HunyuanVideo 950PR 量化的来源性能表](hunyuan_video_950_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [HunyuanVideo A3 累计优化的来源性能观测](hunyuan_video_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [HunyuanVideo 稀疏与 Ring 的来源数据及平台缺口](hunyuan_video_sparse_source_observations.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Hy3-preview A3 分阶段性能与批次口径观测](hy3_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [LongCat-Lite A3 MLA-Prolog 与长输入的来源观测](longcat_lite_a3_prolog_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [LongCat-Lite EP 报告的平台与源码待核验观测](longcat_lite_ep_source_observations.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Qwen3-MoE A3 两条实现的来源时延观测](qwen3_moe_a3_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Sana-Video 来源 A5（950）量化性能观测](sana_video_950_source_benchmark.md)：集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
- [Sana-Video 480p81f 来源时延（平台与精度待核验）](sana_video_bf16_source_observations.md)：保留来源中 A2/A3 合并表的 480p81f 单步和采样时延；表内未绑定具体卡型或 quant_type，不将默认 BF16 配置当作测量精度证据。
- [AutoFuse A3 部分编译与 hc_post 的来源观测](autofuse_a3_source_benchmark.md)：AutoFuse A3 部分编译与 hc_post 的来源观测；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
- [LI/DIA PyPTO 调优的来源观测（测量条件待补）](operator_tuning_source_observations.md)：保留 PyPTO LI 的三项调优披露与 DIA 首版瓶颈比例，目标库支持 A3，但逐次测量环境仍待补。
- [PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）](pypto_v4_operator_source_observations.md)：PyPTO V4 单 die 算子数据与 VF 观测（平台待核验）；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
- [A3 LI TopK 融合与 HcPost 的来源观测](ascendc_a3_li_hcpost_source_observations.md)：分开记录固定 A3 指南的 LI TopK 融合相对收益和 HcPost shape 时延，不将两组测量拼接或外推。
