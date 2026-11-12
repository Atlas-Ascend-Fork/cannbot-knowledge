# 模型部署指南

准备权重、环境与部署前提，保留历史方案的生命周期边界。

- [已停用：LongCat A3 长序列 KVP 的历史条件与配置](kvp_longseq_decode.md)：当前版本不提供 LongCat KVP 配置或部署入口；撤下旧代码、旧 YAML 和多提交历史配方。
- [量化部署：先检查权重格式，再选转换或直载](quant_weight_conversion_path_selection.md)：昇腾量化权重制备与部署路径：离线系数配合 convert_model.py、原始 compressed-tensors 权重直载、amct 重新标定；按模型、格式与平台选择并验收精度。
- [启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）](yuanrong_kv_pool_remote_h2d_ascend_prereqs.md)：依据固定部署文档检查 Yuanrong Remote H2D 的主机 HugeTLB、worker 参数和 NPU/RoCE 环境；关闭开关后仍需验证默认传输，不推导零拷贝次数或设备大页布局。

- [vLLM Ascend D2RH部署：Atlas 850E暂存容量、控制端口与超节点准备](vllm_ascend_d2rh_deployment_contract.md)：按Atlas 850E UBoE与DeepSeek-V4-Flash来源限定D2RH部署，核对pinned CPU arena、host-ready/H2D完成、rank端口、950PR/DT容器和物理NPU端点映射；保留译文版本差异及未知平台draft。 核对 CANN 9.2 前后 route.conf 的挂载条件。
- [vLLM Ascend 外部缓存集成：UCM 架构与 LMCache 版本边界](vllm_ascend_external_cache_integration.md)：区分UCM拓扑与LMCache-Ascend外部注册所有权，结合中文安装旧配方核对版本、设备和配置，避免将旧连接器或宣传倍数当当前部署结果。补充UCM三种配方、端口/长度冲突、0.8预种与来源性能表，以及UCMConnectorV1 reserved hook/外部所有权边界。
- [vLLM Ascend Kthena PD 编排：CRD、资源映射与旧配方验收](vllm_ascend_kthena_pd_orchestration.md)：核对 Volcano Kthena 的 ModelServing、ModelServer、ModelRoute 分工，区分旧镜像、NPU资源名、实际并行和 KV 连接器；保留 Mooncake/nixl 配置差异、heredoc 展开及健康检查的证据边界。
- [vLLM Ascend KV Pool：后端选择、命名空间、内存与故障边界](vllm_ascend_kv_pool_backends.md)：结合当前中文与历史KV Pool页核对A2/A3/950后端能力、逐层依赖、SSD预取/驱逐和每进程预算，区分本地IPC与TCP、Yuanrong预注册与真实数据面证据；补充Qwen2.5-72B双节点多实例、Store别名、JSON与冷/热TTFT实验合同，以及107374182400字节即100GiB的预算。
- [vLLM Ascend 旧版大规模EP模板：DP组、端口与迁移验收](vllm_ascend_legacy_large_ep_migration.md)：审查仍面向v0.9.1的A3大规模EP中文模板，分别核对P端独立DP组、D端全局rank与端口，固定模型/connector/参数版本后再做当前部署验收。
- [vLLM Ascend LoRA 服务：适配器选择、MoE 布局与单槽路径](vllm_ascend_lora_serving.md)：在 A2/A3/310P 核对基础模型和 adapter 的命名、rank、堆叠专家权重及运行时加载，区分单槽融合、通用 BGMV 和 fully-sharded 路径。
- [vLLM Ascend ModelOpt MXFP8：别名、排除层与量化方法选择](vllm_ascend_modelopt_mxfp8_loading.md)：区分mxfp8/modelopt_mxfp8与原生block FP8加载，保留ModelOpt解析器和exclude映射，核对vision回退及Linear/MoE实际scheme。
- [vLLM Ascend Netloader：逐 rank 权重源与量化缓存](vllm_ascend_netloader_weight_transfer.md)：通过 netloader 插件复用已加载实例的权重，核对 SOURCE 优先级、TP 分区、MTP 端口与 INT8 原始参数保存，并用默认加载作基线。
- [vLLM Ascend 量化权重加载：ModelSlim、compressed-tensors 与原生 FP8](vllm_ascend_quantized_checkpoint_loading.md)：从 checkpoint 描述、上游自动识别与 Ascend 重建 quant_config 判断格式和加载路径，保留 310P 独立后端以及文档与固定实现差异。 保留孤儿 Qwen3 32B W4A4 和 Qwen3 8B W4A8 旧工具起点、权重和单 NPU 证据限制。
- [vLLM Ascend Ray 多机启动：通信、资源视图与模型拓扑](vllm_ascend_ray_multinode_bootstrap.md)：以固定Qwen3多机教程区分物理通信、Ray资源发现与真实模型推理，核对启动前环境、共享路径、TP/PP映射和验收，硬件组合保持待确认。
- [vLLM Ascend RFork：兼容 seed、处理后权重与回退生命周期](vllm_ascend_rfork_weight_warmstart.md)：按固定版本核对checkpoint/processed路径、manifest、租约、发布与清理；后续Engram与legacy planner边界不提升成设备运行结果。
- [vLLM Ascend 环境准备：版本配对、硬件镜像与分层验收](vllm_ascend_versioned_environment.md)：区分ceac/3164与5f5发布宏、Native pin和release配对；按硬件选择安装依赖与分层验收，不拼接不同来源版本。

- [推理并行配置选型：按 Prefill、Decode 和模型结构找参考 YAML](parallel_reference_config_selection.md)：Qwen3-MoE 16TP/128EP 与 Kimi PD Prefill/Decode 参考配置，核对 cp_size、o_proj_tp_size、R1/GLM/V3.2/LongCat YAML、DP 本地 batch 和显存通信预算。
