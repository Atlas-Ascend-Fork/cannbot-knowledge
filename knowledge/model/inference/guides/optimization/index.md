# 模型优化指南

分阶段实施优化并验证精度、性能与回退。

- [LLM Decode 图模式：编译配置、backend 定界与精度排查](graph_mode_decode_only_compile_backends.md)：LLM 图模式的 GE/npugraph_ex 编译配置、backend/aot_eager 精度定界、frozen_parameter 冻结与非连续权重、dynamic 长度和版本故障。
- [R1 Prefill 微批双流：按请求切分并对齐通信轮次](prefill_micro_batch_dual_stream_moe_overlap.md)：R1 Prefill microbatch 双流 MoE：按请求边界切 packed 微批，对齐 EP 通信和 chunk 轮次；核对 micro_batch_mode、事件与输出顺序。
- [单卡推理优化指南：分阶段验证 KV、融合算子与 Decode 图模式](staged_single_card_optimize_pipeline.md)：记录来源 model-optimize Skill 的三阶段参考流程：KVCache 与 FA、其他融合算子、Decode 图适配；每阶段对照基线验证，具体阶段是否需要取决于现有实现和瓶颈。
- [多流优化流程：拆解依赖、选择后端并验收真实收益](multi_stream_optimization_workflow.md)：多流依赖、GE/npugraph_ex 后端与 LongCat 编排；HunyuanImage 的 share_mlp_stream 初始化注入、Qwen3-Next patch 案例选型及同步、控核和真实重叠验收。

- [vLLM Ascend AI QoS：A3 网络流量优先级和交换机联动](vllm_ascend_ai_qos_network.md)：结合AI QoS中文资料与两原图区分Strict Priority的SP、通道tag和UB交换机VL，核对A3/DSMI/驱动限制与实际策略，再测拥塞和服务尾延迟。
- [vLLM Ascend AISBench 定时剖析：采集窗口、raw/parsed 与产物完整性](vllm_ascend_aisbench_profile_artifacts.md)：追踪 ProfileSpec、ProfileController 和 profile_manifest，核对正式请求触发、跨节点端点、raw 打包、逐 rank 解析上传和离线合并，区分采集完成与模型性能验收。 补Nightly profiling入口与benchmark键选择、7/90天保留期和GitHub/OBS定位，保留评论解析缺口，分别验收完整trace与性能基线。
- [vLLM Ascend Balance Scheduling：DP 全局准入冻结](vllm_ascend_balance_admission.md)：解释任一 DP rank 达运行请求上限后的全组新请求冻结，核对配置优先级、EngineCore gather 时机和版本漂移。 补清中英签名差异、local active/global running两容量字段、当前pin与Phase2B接缝的适配边界。 说明 CPU tensor 的 item 与 NPU 同步成本的证据边界。
- [vLLM Ascend 离线任务调度：Job 分组、EWMA 与 KV 预留](vllm_ascend_batch_job_scheduler.md)：结合中文离线批处理指南，核对request ID任务分组、EWMA与块/token阈值，记录实际调度类、KV预留和最长等待，保留无防饥饿限制。
- [vLLM Ascend 性能基准：在线、离线与多模态任务的可比测量](vllm_ascend_benchmark_workflow.md)：结合中文指南与基准脚本核对QPS、dummy权重、数据集和指标，保留参数/服务身份、清理范围与失败产物证据，再按同负载评估真实模型性能。 补充 Native Completion 的 TTFT、排队、ITL、tokens_per_second公式与末尾usage发射条件。
- [vLLM Ascend CPP：PD Prefill 流水并行的动态分块与校准](vllm_ascend_cpp_prefill_calibration.md)：在 PP>1 的 PD P 端先建立固定 chunk 基线，再完成在线时延校准并调节动态 chunk，避免未校准预测、前缀命中和 balance 互斥造成误判。
- [vLLM Ascend CPU 绑定：NUMA、cpuset 与 950 特殊路径](vllm_ascend_cpu_numa_binding.md)：结合CPU绑定中文设计与用户指南，核对全局/隐藏NPU份额、ARM默认和950 cluster/UVB路径，分别验收线程、页面、IRQ及部分生效后的实际状态。
- [vLLM Ascend MRv1 动态验证预算：条件置信度、全局分配与同步代价](vllm_ascend_dynamic_verify_budget.md)：沿DynamicSpecScheduler将DSpark/DFlash条件置信度转为累计生存概率和每请求前缀长度，区分budget_k、min_verify_tokens、周期更新与MRv2 adaptive。
- [vLLM Ascend DyntraLB：单机 Decode DP 的暂停与准入均衡](vllm_ascend_dyntra_decode_balancing.md)：结合DyntraLB中文指南，按单机Decode内部DP、KV块负载和下一步计划核对准入/暂停，区分触发阈值、快照区间和保留KV，并做同负载对照。
- [vLLM Ascend EPLB：Runner 分流、专家搬运与负载窗口](vllm_ascend_eplb_runner_and_movement.md)：区分MRv2 STAIR与MRv1配置及中文旧配方，核对参数告警忽略/实际生效、阶段窗口、硬件/量化搬运限制与热点日志，使用真实路由验收EPLB。 补充孤儿 SwiftBalancer 的零开销、容错、冗余等于 TP 及旧经验值的证据边界。 单独说明 EPLB gettext 扁平表格的量化、硬件和列对齐，不能从合并词条恢复全部组合。
- [vLLM Ascend 细粒度 TP：DP 轴分片和四个组件的不同契约](vllm_ascend_finegrained_tp_contracts.md)：按中文四组件合同核对DP轴固定容量与Decode对齐、MoE和图上界/PreemptOffload条件，区分启动降级、构造/采样拒绝及A2来源的显存和TPOT结果。
- [vLLM Ascend GLM KDA RecoverSSM：实验开关、并行限制与回退](vllm_ascend_glm_kda_recoverssm.md)：在A3/A5的GLM-5.3-Flash MRv2中核对--use-replayssm、APC、Mamba缓存和PD约束，区分上游ReplaySSM与Ascend RecoverSSM并验证质量和净时延。
- [vLLM Ascend 图优化流程：ACLGraph、Npugraph_ex 与有效配置验收](vllm_ascend_graph_mode_selection.md)：结合图模式与Npugraph_ex中文设计核对有效配置、硬件门控和FX融合guard，分开验收运行时捕获、static/Super Kernel及Xlite路径。
- [vLLM Ascend KVPP：用分层缓存与广播换取长上下文容量](vllm_ascend_kvpp_capacity_tradeoff.md)：对照KVPP中文旧版与当前设计，核对TP×PCP层所有权、固定K和动态K的模型约束及图/connector门槛，分开裁决950DT容量、时延吞吐与实验状态。
- [vLLM Ascend MS Service Metric：provider、YAML与Prometheus进程域](vllm_ascend_ms_service_metric_provider.md)：按 get_metric_provider、MetricProvider 与 MS_SERVICE_METRIC_CONFIG_PATH 接入运行指标，核对provider声明、YAML符号、Core版本、Prometheus进程目录和配置重载，限定V1/EPLB插桩范围。
- [vLLM Ascend MS Service Profiler：符号配置、版本与框架链路采集](vllm_ascend_ms_service_profiler_contract.md)：说明 SERVICE_PROF_CONFIG_PATH、PROFILING_SYMBOLS_PATH、generate_service_profiling_config 的版本与符号合同，区分时间线和独立 Metric 与 Prometheus，关联 recorder 旧值和链路完整性排查。 补充 profiler_step_num 与 torch_prof_step_num 的零值差异。
- [vLLM Ascend 短请求优先：Prefill 队列、公平性与阈值调优](vllm_ascend_prefill_short_request_first.md)：在 FCFS Prefill 或混部部署使用 ShortRequestFirst，按真实 prompt 分布和长请求等待尾部设阈值，识别 D 端、batch-job 与 CPP 的组合限制。补充中文profiling-chunk旧译文兼容性裁决、CPP组合与队列安装边界。
- [vLLM Ascend Score Encoder Cache：频率时钟、晋升阈值与双层预算](vllm_ascend_score_encoder_cache_policy.md)：解释 ScoreEncoderCacheManager 的score、promote_percentile、watermark和请求引用，区分CPU slots、NPU驻留、临时copy与ECCPU FIFO，限定理论成本及V1/V2消费边界。
- [vLLM Ascend SP MoE：FlashComm 门控与有效 token 布局](vllm_ascend_sequence_parallel_moe.md)：说明 SP MoE 的 FlashComm 开关、DP1/TP/EP 门控与中文 PO 对照，核对 all-gather 后 unpad、zero-pad、TP2/4/8 融合及平台待核验边界。
- [vLLM Ascend 服务剖析：profiler_config、采集端点与 PD 实例定位](vllm_ascend_service_profiling.md)：从固定文档与 Worker 消费路径说明 TorchNPU Profiler 的启用、端点控制、数据解析与 PD 独立采集，区分算子层和服务框架层证据。
- [vLLM Ascend 投机解码：方法、Runner、验证器与动态 K 选型（含 MTP 概率恢复）](vllm_ascend_speculative_method_selection.md)：按MRv1/MRv2和固定版本区分方法、草稿checkpoint、采样分布与图模式；保留DFlash2后续图/滑窗变化及质量性能验收。
- [vLLM Ascend Suffix Decoding：A2四卡Qwen3-32B与SLO评测口径](vllm_ascend_suffix_decoding_contract.md)：限定A2四卡Qwen3-32B的Suffix Decoding配方，核对Arctic依赖、名义K=3与CPU草稿接线，区分18行来源性能表的TPOT倒数增益、延迟下降和SLO条件。
- [vLLM Ascend 系统调优：TCMalloc、NPU allocator、HCCL 与主机配置](vllm_ascend_system_tuning_contract.md)：按进程、容器和宿主机区分性能候选；核对 PYTORCH_NPU_ALLOC_CONF 的默认追加、sleep/RL 约束及有效环境，记录 TCMalloc、队列、通信和 OS 配置的验证与回退条件。

- [kernel_details 字段解读：流水指标、控核与多流真实重叠](kernel_details_field_interpretation.md)：kernel_details.csv 字段解读：OP State 是执行状态，不能当作精度检查 pass/fail；区分 Type 的 HCCL/AI_CORE 与 Accelerator Core，解释 aic_mac_ratio、aic_mte2_ratio、aiv_mte3_ratio、时间、核数与重叠。
- [Profiling 产物识别：torch_npu ascend_pt 与原生 msprof 目录](npu_profiling_artifact_layouts.md)：找到 kernel_details/trace_view 或 op_summary/msprof 配对文件，核对采集 run、phase、rank 与 device，避免混合多卡数据。
- [NPU Profiling 采集：ProfilerManager 窗口、Level1 与指标配置](npu_profiling_collection_and_metrics.md)：NPU Profiler 只生成基本计数或基础指标、缺流水利用率时，核对 Level1、PipeUtilization、record_shapes 和手动采集窗口；另列 CANN Executor 的 ProfilerManager 配置。

- [SuperKernel 范围分析：依赖边界、受控基线与融合验证](superkernel_scope_analysis_and_validation.md)：从模块、整层到跨层选择 SuperKernel scope，识别动态控制流和分流控核边界；在相同 GE 配置下比较预热后的中位数、波动、编译产物和精度。

- [SGLang 昇腾性能优化指南](sglang_ascend/index.md)：共 9 张知识卡（如 SGLang 昇腾 attention 后端与混合 GDN 的选择边界、SGLang 昇腾在线与离线性能评测的接口和指标、SGLang Ascend 环境变量：框架、DeepEP与DSPARK路径的作用域 等）。
