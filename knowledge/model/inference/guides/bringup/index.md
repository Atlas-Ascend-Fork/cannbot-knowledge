# 模型跑通指南

按步骤完成适配和精度验收。

- [上游 DiT/视频生成模型搬昇腾：运行时 monkey-patch 层替代 fork + 版本门控融合算子替换](upstream_dit_video_monkeypatch_npu_adaptation.md)：当前Sana导入兼容补丁、必传quant_type的方法注入时序、加载后权重同步与量化替换。

- [vLLM Ascend GDN310P数值验收：Golden、状态观察与覆盖缺口](vllm_ascend_310p_gdn_numerical_validation.md)：为310P GDN选择数值验收层，区分V310算子直调、Torch绑定和参考函数，核对Golden递推、输出与state及测试覆盖，避免将局部证据当整链路结果。
- [vLLM Ascend 精度验收：评测工具、数据口径与模型回归合同](vllm_ascend_accuracy_evaluation_contract.md)：核对AISBench、EvalScope、lm-eval与OpenCompass的中文评测、数据和答案解析，审查回归有效参数与相对容差，区分lm-eval报告的ACLGraph配置标记和实际capture/replay证据。
- [vLLM Ascend Attention与量化回归：数值、布局和调用分支测试矩阵](vllm_ascend_attention_quant_test_matrix.md)：为Attention、MoE、量化和kernel warmup变更选择固定UT，定位shape/dtype、缓存别名、PCP/DCP元数据、注册分派及异常门禁；只记录断言合同，不将mock或测试存在提升为NPU结果。
- [vLLM Ascend CI构建产物：缓存身份、镜像与Wheel Variant合同](vllm_ascend_ci_artifact_build_contract.md)：区分Csrc持久缓存、构建环境、nightly测试镜像和Wheel Variant发布产物，核对source/SoC/toolchain身份、降级无L1、动态库排除及variant元数据；不把打包成功提升为设备兼容或模型通过。 补充固定3164的依赖/镜像、共享临时目录Actions staging与CI登记边界。
- [vLLM Ascend 社区贡献：Issue分类、治理角色与交付](vllm_ascend_contribution_issue_contract.md)：社区协作中核对Issue状态、类型、owner、治理与历史名录，按实际标签和反馈工作流解释进度，为适配与性能任务保留独立验收证据。
- [vLLM Ascend分布式缓存回归：传输、租约、PP布局与失败恢复矩阵](vllm_ascend_distributed_cache_test_matrix.md)：为AscendStore、Mooncake、EC、D2RH、KV offload、EPLB和权重传输选择固定UT，核对buffer注册、物理层边界、异步完成、重复/失败与资源寿命；不把mock或结构断言提升为实际通信成功。
- [vLLM Ascend E2E配置证据矩阵：模型、并行、任务与负载选择](vllm_ascend_e2e_configuration_evidence_matrix.md)：从固定测试配置选择模型与量化、TP/PP/PCP/DCP和精度/性能场景，区分模型家族名、实际checkpoint、模板参数及未执行的支持声明；保留多模态、ASR、奖励模型和小型fixture的证据边界。
- [vLLM Ascend 诊断证据：环境采集、日志层级与文件轮转](vllm_ascend_environment_and_logging_evidence.md)：解释collect_env的实际采集范围、失败/缺字段与版本SHA限度，核对Ascend日志模块覆盖、root级别、热更新、路径和20MiB轮转，避免将诊断输出当推理验收。
- [vLLM Ascend代理示例：长度分桶、EPD/PD与请求生命周期](vllm_ascend_example_proxy_orchestration_contract.md)：核对长度分桶、EPD/PD路由及请求生命周期；区分两种代理的首包后重试行为，解释recomputed续写预算与清理，再按固定3164选择prefill会话亲和。示例启发式不证明实际KV命中或恰好一次交付。
- [vLLM Ascend FAQ诊断：版本旧配方、OOM、捕获异常与PA前置条件](vllm_ascend_faq_diagnostic_boundaries.md)：按faqs.po与当前代码区分FAQ旧版本声明、OOM/preemption、Mooncake初始化失败、207008捕获错误和PA选路；保留单次失败、文本匹配及未知硬件边界。
- [vLLM Ascend 首次推理：硬件分支、离线断言与在线响应验收](vllm_ascend_first_inference_acceptance.md)：按A2、A3、310P（Atlas 300I DUO/200I Pro）和950DT的Qwen3-0.6B示例验收首请求，区分容器导入、模型列表、离线非空输出、在线choices文本及退出日志；保留ModelScope和进程身份边界。 核对旧根 quick_start 孤儿译文的成功层次、ModelScope 权重身份与 DUO 图限制。
- [vLLM Ascend 图后端精度验收：3-token logprob 与 Xlite 测试边界](vllm_ascend_graph_logprob_validation.md)：按 compare_logprobs、_COMPILATION_KEYS 和 prefill/decode 判据核对 eager 基线、top-20单向cross-lookup、容差及输出数量；区分Xlite单卡数值检查、双卡非空smoke与UT占位。
- [vLLM Ascend Csrc 缓存：L0/L1 身份、选择性失效与安全回退](vllm_ascend_incremental_build_cache.md)：结合中文构建缓存设计区分快照键与凭据、L0/L1命中和实际编译复用，核对身份、CI相对路径、并发发布和成功后清理的独立边界。
- [vLLM Ascend MemFabric初始化、注册与字节传输探针](vllm_ascend_memfabric_transport_probe_contract.md)：说明 GlobalMemfabricTE 的角色/协议锁定、一次性内存注册及 test_memfabric_pd_read 的控制面、数据一致性和清理证据。
- [vLLM Ascend模型与API端到端验证：输出、缓存命中、投机和状态切换矩阵](vllm_ascend_model_api_e2e_test_matrix.md)：按固定PR/E2E测试选择真实模型和API场景，区分响应结构、输出质量、投机指标、缓存命中、weight-update oracle与设备状态；保留输入、拓扑、skip和真实运行结果的边界。
- [vLLM Ascend 模型教程：YAML命令生成与适配交付](vllm_ascend_model_tutorial_codegen.md)：按model-code元数据选择五种converter，核对YAML配置、位置变量、shell文本和生成脚本身份；结合模型教程模板保存版本、权重、硬件与真实功能/精度/性能证据。
- [vLLM Ascend模型与Worker回归：加载、投机、缓存和310P测试矩阵](vllm_ascend_model_worker_test_matrix.md)：为模型加载、MRv1/MRv2、投机采样、LoRA与310P变更选择固定UT；核对checkpoint身份、CPU计数、共享cache/参数所有权、图模式与异常恢复，区分mock合同和真实权重/NPU验证。
- [vLLM Ascend 多节点测试：LWS、内部与外部DP及运行证据](vllm_ascend_multi_node_test_contract.md)：按multi_node配置选择internal/external运行时，核对LWS与本地主机、节点rank/设备预算、LOG_PREFIX和就绪顺序，保留pytest/AOP返回、各节点日志及benchmark产物的限定。
- [vLLM Ascend原生构建生成：CMake依赖、OpDesc与模板接口合同](vllm_ascend_native_build_generation_contract.md)：定位Csrc编译/UT/符号与配置生成的实际入口，区分CANN头库发现、INI/JSON/tiling参数生成和Opgen模板；保留caller、缓存语义输入、Device及第三方构建未验边界。
- [vLLM Ascend静态接口门禁：版本区间、调用与返回协议及skip语义](vllm_ascend_native_interface_static_gate.md)：使用固定接口分析器的公开合同解读Native区间对Ascend的override、import、direct-call和返回值影响，区分新增破坏、历史不兼容与unknown；核对fail-on和pytest将introduced break转skip的边界。
- [vLLM Ascend原生包安装：版本检查、文件布局与多版本生命周期](vllm_ascend_native_package_install_contract.md)：区分Csrc版本声明、CANN包前缀校验、Docker/pyproject依赖及安装器filelist/多版本状态，定位ops-transformer/opapi路径、环境与清理入口；不执行或推导目标机兼容。
- [vLLM Ascend 新模型适配：架构注册、prefix、权重与分阶段验收](vllm_ascend_new_model_onboarding.md)：对照中文历史指南与 vLLM v0.32.0，核对 embed_input_ids、Attention 导入、惰性注册、prefix 和权重/状态协议；注册、dummy、真实模型精度与性能分别验收。 补充 Qwen2.5 Omni 的 registry 别名、Thinker 与输入表分层实例。 补充 v0.32 CLI 预检：FlexibleArgumentParser、重复参数告警、JSON合并、ModelDType及服务模型名与权重路径。 补充 Native API 模型与LoRA预检、准入、流式错误和请求身份的分阶段验收。
- [vLLM Ascend Nightly CI：命令派发、PR矩阵与回归证据](vllm_ascend_nightly_ci_dispatch_contract.md)：用/nightly、workflow_dispatch与nightly_config定位实际测试，区分PR SHA、工具和模型配置，核对维护窗口、all/560T筛选、accuracy组及profiling参数缺口，再按真实run与产物验收。
- [vLLM Ascend设备算子验证：golden、布局、有效行与容差矩阵](vllm_ascend_npu_operator_test_matrix.md)：为Ascend自有算子与Triton路径选择固定nightly数值测试，区分逐位copy、有限性、cosine、绝对/相对容差和多卡结果；保留设备skip、独立reference及未执行的性能/Operator边界。
- [vLLM Ascend离线示例：Prompt Embeds、指标、重载与RL状态验证](vllm_ascend_offline_api_example_contract.md)：核对固定离线示例的模型输入、pooling/audio、request指标、DP launcher、sleep和权重更新顺序，区分打印演示、结构断言及真实checkpoint/NPU质量证据。 补充固定3164 checkpoint坐标稀疏HCCL与失败后暂停恢复边界。
- [vLLM Ascend auto_bisect 回归定位：端点、依赖、构建与多节点判据](vllm_ascend_regression_bisect_contract.md)：按固定二分工具追踪整份 YAML、first-parent 提交、依赖漂移、构建身份、跨节点屏障和状态恢复，区分已确认回归与 SKIP 嫌疑区间，避免只按 first_bad_commit 或退出码下结论。
- [vLLM Ascend版本回归清单：发布声明、缓存恢复与适配重验](vllm_ascend_release_regression_watchlist.md)：按固定版本release fragments建立模型迁移回归检查点，区分版本限定的支持声明、真实实现约束与尚未执行的精度/性能证据；核对KV恢复、PP物理层、KDA状态、Mooncake失败及环境身份。
- [vLLM Ascend 请求探针与多模态断言合同](vllm_ascend_request_probe_evidence_contract.md)：解释 send_request 与 send_mm_request 的 token 预算、HTTP 行为、图像装载和断言边界，帮助 Agent 将探针输出与服务质量证据分开。
- [vLLM Ascend运行控制回归：平台门禁、调度、图、诊断与构建工具矩阵](vllm_ascend_runtime_control_test_matrix.md)：为平台能力、scheduler、图编译、runtime config/guard、CPU绑定、构建缓存与性能工具选择固定UT；定位异常、状态恢复、缓冲身份和产物完整性，保留CPU mock及工具自测与NPU/业务证据之间的边界。
- [vLLM Ascend 测试证据选择：CPU、NPU、精准CI与文档用例](vllm_ascend_test_evidence_selection.md)：按固定上游测试指南区分mock、真实设备、E2E和性能证据，核对精准选择与runner路由、缩层随机权重、文档固定代码块及实际触发方式。 补充 /e2e 的派发鉴权、双版本、skip/accuracy 路由及贡献交付边界。
- [vLLM Ascend调优配方：投机K、专家重排与量化校准证据](vllm_ascend_tuning_recipe_calibration_contract.md)：区分离线goodput最优K、示例EPLB规划、llm-compressor校准/动态量化和发布recipe硬件声明，核对测量输入、conditional概率口径、checkpoint目标与版本化部署边界。
