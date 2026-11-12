# SGLang 昇腾性能优化指南

本目录收录固定版本来源支持的知识；具体平台、配置和验证边界见各卡正文。

- [SGLang 昇腾 attention 后端与混合 GDN 的选择边界](sglang_ascend_doc_attention_selection.md)：区分 full attention、MLA、GDN 和多模态接口，保留新旧支持表与页大小/树候选冲突。
- [SGLang 昇腾在线与离线性能评测的接口和指标](sglang_ascend_doc_benchmark_method.md)：按文本、多模态、Embedding 选择测试入口，区分 TPOT/ITL、客户端并发、token口径和示意输出。
- [SGLang Ascend 环境变量：框架、DeepEP与DSPARK路径的作用域](sglang_ascend_doc_environment_layers.md)：区分MLAPO/FIA NZ、多流、权重格式、DeepEP分组缓冲、MemFabric和DSPARK目标/draft注意力开关，避免以同名变量推导跨层保证。
- [SGLang 昇腾 EP 模式与分轮通信配置的文档边界](sglang_ascend_doc_expert_parallel_selection.md)：按混部和PD角色选择DeepEP/fuseep，保留融合范围、EPLB、EP/TP和缓冲公式的适用限制。
- [SGLang Ascend 算子性能诊断：task指标、流水与搬运假设](sglang_ascend_doc_operator_profiling.md)：从msprof示例提炼task时长、Vector/Scalar/MTE与pipeline占比读法，区分单次源码记录、优化假设和需要按产品核实的硬件常数。
- [SGLang Ascend 调参：按角色预算内存、通信与图覆盖](sglang_ascend_doc_parameter_tuning.md)：以DeepSeek-V3.2 A3配方为参照，串联TP/AttentionDP/CP、DeepEP容量、图batch、投机和缓存的决策顺序，保留兼容矩阵的部分/未知状态。
- [SGLang 昇腾量化的格式选择、自动识别与验证边界](sglang_ascend_doc_quantization_selection.md)：按 A2/A3/950 区分 ModelSlim、MXFP8、MXFP4 与 GGUF，并保留在线离线路径及文档冲突。
- [SGLang 昇腾服务的 Profiler 采集、落盘与图模式边界](sglang_ascend_doc_service_profiling.md)：使用 API、benchmark 或 CLI 采集 NPU trace，区分自动停止、异步解析、图模式和多节点合并限制。
- [Wan2.1 的 Ring-SP 上游单案例性能观测](sglang_ascend_doc_wan_ring_sp_observation.md)：保留 torch_npu 2.10 下单NPU与双NPU Ring-SP 的工作负载、阶段耗时和重复信息缺口。
