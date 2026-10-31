# 模型专用指南

- [Qwen3-Next Atlas A3 推理部署与优化指南](qwen3_next_atlas_a3_deployment.md)：面向 Atlas A3 上 Qwen3-Next 推理部署，说明 CP/TP/EP 并行、GDN 融合 Kernel、MTP、W8A8C8、ACLGraph 的使能条件、互斥关系和验证边界。

- [DeepSeek-V4 A3与950部署及优化验收流程](deepseek_v4_deployment.md)：更新 V4 当前环境与六类启动配置，串联 CacheEntry/CP 状态写回、原生 MTP、950 低时延 TP 和 DSpark 验证。
- [LongCat-Flash A3 部署与优化验收流程](longcat_flash_deployment.md)：当前 LongCat A3 统一 Executor 启动、五类配置、复数多流开关、GE/npugraph_ex 边界、AFD/MTP 与验收。

- [DeepSeek-R1 A3 分阶段部署与优化验收流程](deepseek_r1_deployment.md)：更新R1当前A3软件、统一入口和配置字段，区分普通/长序列MTP与人工EPLB基准，并核对packed Prefill预算。
- [DeepSeek-V3.2-Exp A3 长序列部署与验收流程](deepseek_v3_2_exp_deployment.md)：更新当前Docker环境、六份YAML、统一Executor和真实后端/CP/offload约束，删除acl_graph旧配方。
- [Gemma-4 文本 Decoder 当前部署](gemma4_26b_a4b_deployment.md)：当前gemma_4入口、单一Decode配置、Page cache混合布局与等长限制、MC2/图后端和RoPE验收。
- [GLM-5 当前部署：A3 W8A8 与 950 MXFP8](glm_5_deployment.md)：更新GLM-5当前Docker/统一字段、A3与950配置，区分整数量化、MXFP8和被禁止的offload组合。
- [GPT-OSS A2 权重准备与 TP 推理验收流程](gpt_oss_deployment.md)：当前GPT-OSS的sink/滑窗与clamped GLU、packed/Page cache和独立TP组；部署以BF16、batch1/eager示例验收。
- [HSTU A2 推荐推理接入、缓存与并行验收流程](hstu_deployment.md)：HSTU A2 推荐推理接入、缓存与并行验收流程，串联固定版本配置、来源冲突、精度与性能验证以及回退入口。
- [HunyuanImage-3.0 A2/A3 并行接入与验收流程](hunyuan_image_3_deployment.md)：当前HunyuanImage的统一YAML、CFG每rank缓存修正、融合布局、A2回退与实际精度/稳态验收边界。
- [HunyuanVideo 分版本的并行、稀疏与量化验收流程](hunyuan_video_deployment.md)：当前Hunyuan统一六类YAML、环境、权重、Ring稀疏/LSE与缓存/量化边界，去除跨版本混配。
- [Hy3 A3/950 当前部署与 MTP 验收](hy3_preview_deployment.md)：当前Hy3三类MTP配置、A3/950环境、FP8/AMCT权重、SP/PA/NZ和源码与旧基础报告差异。
- [Kimi-K2-Thinking A3：当前统一 Executor 部署](kimi_k2_thinking_deployment.md)：更新当前A3环境、kimi_k2_thinking.yaml、统一启动入口和真实custom_params，撤回旧私有runner与过时规模表。
- [LongCat-Lite A2/A3 的 TP、EP 部署与验收流程](longcat_flash_lite_deployment.md)：当前四类Lite配置、统一离线入口、已实现SP、MC2回退、无旧Prolog开关、GE多流及文档/源码差异。
- [Qwen3.5-MoE A3/950 当前部署](qwen3_5_moe_deployment.md)：当前Qwen3.5环境、batch32/4/1与950量化、原生GDN/Mamba状态、纯EP/TP及真实守卫，撤下旧fallback。
- [Qwen3-MoE 当前自研与 SGLang 部署](qwen3_moe_deployment.md)：当前A3/950与SGLang分立部署、三类量化/Hadamard、精确Prefill门控及已迁移的统一入口和缓存。
- [Qwen Dense A2/A3 当前部署与量化验收](qwen_dense_deployment.md)：当前Qwen Dense六类YAML、W8A8全量化导出与融合MLP、共享执行器和分阶段来源性能验收。
- [Sana-Video NPU 适配、量化与生成验收流程](sana_video_deployment.md)：当前Sana补丁时序、必传quant_type、加载后量化替换、本地离线权重、DP和950混合位宽验收。
- [Wan2.2-I2V 当前部署与验收](wan2_2_i2v_deployment.md)：当前A2/A3/950部署、统一三类YAML、CFG2默认与CFG1性能表差异、单卡缓存和多卡强制NoCache。

- [DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载](deepseek_v4_1_flash_single_npu_offload.md)：区分 Host 随机查表与 CPU 专家计算，按 HBM、Host/NUMA 内存、重叠窗口和热专家覆盖率评估 950 单卡部署。

- [DeepSeek-V4 Flash DSpark 部署与拒绝采样验证](deepseek_v4_dspark.md)：基于最新 V4 的 DSpark 配置，核对固定宽度 Verify、拒绝后的缓存位置、A3/950 算子条件与 PD 概率状态传输。
- [GLM-5.3-Flash 950DT 部署与验收](glm_5_3_flash_950_deployment.md)：基于当前8卡EP样例准备算子与Hybrid权重，限定TP/CP、npugraph_ex和共享专家多流，并按输入、精度和时延验收。
- [LongCat-Next A3 多模态离线推理](longcat_next_a3_multimodal.md)：说明 A3 上 LongCat-Next 六类任务的请求清单、媒体路径、TP/EP、生成头图模式及结果验收，区分多模态与纯文本入口。
