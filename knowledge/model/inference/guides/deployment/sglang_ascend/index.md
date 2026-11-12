# SGLang 昇腾安装、部署与评测文档

- [SGLang Ascend 安装：分平台组件版本组与历史文档差异](sglang_ascend_doc_installation_version_sets.md)：对齐A3/950的CANN9.1.0组件组、Python3.12、TorchNPU、MemFabric和NPU Kernel，保留旧A2/A3 CANN8.5说明的边界，并定义服务与PD验收入口。

- [SGLang Ascend MemCache作为L3缓存的部署与配置边界](sglang_ascend_cache_memcache_deploy.md)：说明HiCache接入npu_memcache所需的Meta与Local服务、Ascend IO布局组合、容量与world_size约束，以及配置解析失败的区分。
- [SGLang Ascend 精度验收：sgl-eval与EvalScope的在线文本/多模态流程](sglang_ascend_doc_accuracy_evaluation.md)：以A3示例区分GSM8K/MMLU的sgl-eval入口和其他数据集的EvalScope调用，明确服务路由、模型ID、TLS/代理故障与验收产物。
- [SGLang Diffusion NPU注意力文档：旧SDPA与新FA路线](sglang_ascend_doc_diffusion_attention_versions.md)：对比旧文档NPU仅SDPA和新版本Ring FA、组件/角色覆盖及NPU稀疏后端，保留版本边界。
- [SGLang昇腾命令生成器：卡数、容器与验证徽标](sglang_ascend_doc_diffusion_builder_devices.md)：说明A3双die和950单设备计数、NPU挂载，以及生成器状态和CPU字符串测试不能代替运行验证。
- [SGLang Diffusion Cosmos3昇腾启动：Guardrail权重加载边界](sglang_ascend_doc_diffusion_cosmos_guardrail.md)：记录可选Guardrail依赖、NPU UnpicklingError来源处理和模型启动与质量验证的区别。
- [SGLang Diffusion昇腾分离部署：传输构建与GLM token派发](sglang_ascend_doc_diffusion_disaggregation.md)：区分Mooncake Ascend Direct环境和GLM-Image不搬latent的14去噪worker拓扑，保留不同数据面的边界。
- [SGLang Diffusion FLUX昇腾配置：版本与资源计数](sglang_ascend_doc_diffusion_flux.md)：区分FLUX1/FLUX2的A2/A3生成器配置、旧A3基准和未验证HTTP组合。
- [SGLang Diffusion MiniMax-H3昇腾配方：驻留、TP/SP与有损缓存](sglang_ascend_doc_diffusion_h3_topology.md)：保留4/8 NPU LASER配方和单次历史延迟，说明请求quality覆盖及无缓存基线。
- [SGLang Diffusion HunyuanImage3昇腾边界：TP分片与未验证组合](sglang_ascend_doc_diffusion_hunyuan_image.md)：说明四NPU TP4等价启动、encoder/VAE复制及SP/CFG并行未接入，避免容量估算当峰值实测。
- [SGLang Diffusion昇腾安装入口：同包引擎与版本证据](sglang_ascend_doc_diffusion_installation.md)：对齐新旧文档中的diffusion extra、NPU安装分流和A2/A3总声明，避免把NVIDIA容器当NPU环境。
- [SGLang Diffusion Qwen-Image：A3两种并行配置的证据差别](sglang_ascend_doc_diffusion_qwen_image.md)：保留生成器TP1/SP2与cookbook TP2/SP1不一致、A2资源及未验证HTTP组合边界。
- [SGLang Diffusion GLM-Image远程AR：HCCL端口与调用成本](sglang_ascend_doc_diffusion_remote_ar.md)：说明SRT按完整AR生成发送HTTP、启动连接检查、A3共卡双服务端口隔离及T2I能力边界。
- [SGLang Diffusion SenseNova昇腾配方：融合预热与批次测量](sglang_ascend_doc_diffusion_sensenova.md)：说明首次SwiGLU打包预热、FIA/norm条件回退及910C历史B1/B2数据的可比边界。
- [SGLang Diffusion Wan2.1：昇腾型号、变体与缓存基准](sglang_ascend_doc_diffusion_wan21.md)：说明1.3B/14B的生成器资源选择及A3历史TP2/SP2四设备配置，避免跨配置计算缓存收益。
- [SGLang Diffusion Wan2.2：级联变体、8设备LASER与验收](sglang_ascend_doc_diffusion_wan22.md)：说明A14B和TI2V5B不同资源公式、来源A3 TP2/SP4配置及缓存并发结果的负载边界。
- [SGLang Diffusion Z-Image-Turbo：A2/A3资源与CFG成本](sglang_ascend_doc_diffusion_zimage.md)：说明小模型标准设备配置、8步与Turbo默认无负分支，以及缓存近似和未验证组合。
- [SGLang 昇腾功能选型与支持矩阵冲突](sglang_ascend_doc_feature_support_contract.md)：合并新旧 NPU 功能表，保留平台特例、GPU专用项、计划功能和同版本矛盾。
- [SGLang 昇腾自定义算子的集成与版本对齐](sglang_ascend_doc_kernel_integration_workflow.md)：区分 Ascend C torch op 和 Triton Python 调用，记录 schema、workspace、包版本与设备测试边界。
- [SGLang MindSpore 后端的安装、运行和版本冲突](sglang_ascend_doc_mindspore_backend.md)：合并两仓 MindSpore 文档，保留独立包、模型范围、CANN8.3/8.5冲突和通信/Protobuf排障。
- [SGLang 昇腾新模型与外部多模态包的接入流程](sglang_ascend_doc_model_adaptation_workflow.md)：从 ForwardBatch、RadixAttention 到外部 EntryClass/processor 注册，保留 NPU 对照验证和热路径要求。
- [SGLang 昇腾模型支持矩阵的使用与新旧差异](sglang_ascend_doc_model_support_evidence.md)：按具体 checkpoint 读取 A2/A3 支持声明，区分模型接入、优化组合和950证据缺口。
- [SGLang 昇腾 PD 传输、实例端口与角色配置](sglang_ascend_doc_pd_transfer_selection.md)：融合两仓PD文档，区分MemFabric版本、Mooncake激活、物理设备映射和P/D分组。

- [SGLang 昇腾集群测试模板的设备、网络与共享目录前提](sglang_ascend_cluster_pod_templates.md)：区分 Volcano 与 green StatefulSet、设备资源计数、hostNetwork 和共享源码挂载，说明 PD 模板迁移的验证边界。
