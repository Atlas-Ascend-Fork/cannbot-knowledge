# SGLang 昇腾评测与回归测试合同

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang NPU任务精度回归的模型与采样配方](sglang_ascend_doc_validation_accuracy_recipes.md)：汇总GPQA、AIME、GSM8K及MMMU注册配置，标出PR数据集切换、禁用测试、CP注释与文件名不等于真实负载的差异。
- [SGLang NPU接口与采样测试的断言边界](sglang_ascend_doc_validation_api_cases.md)：整理token ID、FIM、logprob、thinking、stop和Profiler等NPU回归，区分协议断言、数值比较与仅HTTP smoke。
- [SGLang NPU缓存与PD回归的命中和时延断言](sglang_ascend_doc_validation_cache_pd.md)：区分Radix/HiCache命中、Mamba L3回读、PD主机池解析与TTFT相对门槛，避免把测试存在当成验证结果。
- [SGLang NPU训练回放所需indexer topk响应测试](sglang_ascend_doc_validation_indexer_capture.md)：保留DeepSeekV4与GLM5.2 dummy六层的indexer topk形状和下界断言，明确未验证排序、上界和训练等价性。
- [SGLang NPU语言模型回归配方与GSM8K目标矩阵](sglang_ascend_doc_validation_llm_matrix.md)：汇总A2/A3注册及Gemma4手工语言测试的并行、量化和质量目标，保留CP停用注释及继承参数边界。
- [SGLang昇腾手工大模型量化与草稿预取测试配方](sglang_ascend_doc_validation_manual_advanced.md)：保留DeepSeek MLA C8、GLM草稿预取、Kimi K3双机及MiMo DFLASH/多层EAGLE手工测试的精确配置和证据边界。
- [SGLang NPU并行、DeepEP与EPLB测试配方](sglang_ascend_doc_validation_parallel_ep.md)：归纳DP负载均衡、DeepEP auto/低时延、专家记录及offload测试，保留随机抽样和仅smoke的断言范围。
- [SGLang NPU模型性能回归的声明负载和基线](sglang_ascend_doc_validation_performance_recipes.md)：保存DeepSeek、Kimi和Qwen性能测试的TP/DP、长前缀、多模态shape、并发和目标字段，明确这些不是实测收益。
- [SGLang NPU权重量化回归的模型与质量门槛](sglang_ascend_doc_validation_quant_cases.md)：对齐AutoRound、GPTQ、GGUF和W4A4测试的checkpoint、TP与GSM8K目标，避免量化格式名直接等于兼容性或性能收益。
- [SGLang NPU图、调度和内存回归的实际检查范围](sglang_ascend_doc_validation_runtime_cases.md)：说明TP/FIA/图精度、禁chunk和overlap组合、warmup及17GiB启动内存门槛，识别未使用的性能字段。
- [SGLang NPU推测解码回归与950原生block-FP8用例](sglang_ascend_doc_validation_speculative_cases.md)：保留EAGLE3多卡、token map、dummy draft和950 NEXTN FP8草稿测试定义，区分草稿参数、实际启用和质量断言。
- [SGLang NPU视觉语言模型质量与ViT批处理回归配方](sglang_ascend_doc_validation_vlm_matrix.md)：保存MMMU模型目标、TP覆写和图像顺序缓存回归的shape，区分继承默认与视觉质量断言。
- [SGLang NPU端到端精度门槛、EvalScope结果解析与重试](sglang_ascend_test_accuracy_thresholds.md)：说明AIME/GPQA按允许错题数放宽、其他数据集0.99相对阈值、首数据集决定策略以及报告JSON优先和百分号归一化。
- [SGLang NPU公共压测工具的预热、完成数与泄漏日志边界](sglang_ascend_test_benchmark_lifecycle.md)：说明run_bench_serving默认内层1请求预热及可选额外16请求压测、完成数断言、后台任务生命周期，以及内存泄漏测试只扫描日志不能替代显存/页账审计。
- [SGLang NPU测试环境重现与CI覆盖证据边界](sglang_ascend_test_ci_reproducibility.md)：说明CI依赖版本、源码与镜像包混用、可见设备转换、AST注册和enabled/nightly过滤，区分套件选择、运行记录和硬件通过。
- [SGLang NPU集群测试产物的状态、基线与源码身份](sglang_ascend_test_e2e_artifacts.md)：说明E2E harness的single/PD-mix/PD-separation资源区别、运行隔离、日志metric与baseline分离和metrics.json状态不等于技术验收。
- [SGLang NPU嵌入、奖励和VLM测试的断言强度](sglang_ascend_test_embedding_reward_scope.md)：区分Embedding短prompt断言、NoHF Reward类型检查与Gemma HF分数对拍，保留VLM默认MMMU和图模式边界。
- [SGLang NPU精度测试的PR smoke、容差和重试口径](sglang_ascend_test_gsm8k_contract.md)：区分NPUGSM8KMixin的单请求PR smoke与完整评测、0.99相对容差、默认最多3次尝试和EvalScope历史采样基线。
- [SGLang NPU多节点PD测试的角色、实例分组与服务地址](sglang_ascend_test_multinode_pd_harness.md)：说明Kubernetes测试按pod编号和nnodes构造P/D实例、MemFabric store与bootstrap端口映射、router只注册实例master及ready信号的边界。
- [SGLang NPU性能门槛的单位、接受率和缓存命中判定](sglang_ascend_test_performance_contract.md)：说明bench-serving与AISBench指标解析、TPOT门槛误注释、吞吐与时延容差、投机接受长度归一化以及缓存分层命中缺失必须失败。
- [SGLang NPU输出投影微基准的stride、图重放与在线更新校验](sglang_ascend_test_wo_a_measurement.md)：说明DSV4 wo_a einsum和F.linear比较的共享输入/独立层权重、事件计时中位数、真实stride及图内原地权重更新验证范围。
- [SGLang NPU压测输入的自然文本、共享前缀与长度复核](sglang_ascend_test_workload_generation.md)：说明固定token文本生成、全相同前缀对DSpark接受率的影响、AISBench缓存数据文件复用风险及输出长度生成不等于实际服务负载。
