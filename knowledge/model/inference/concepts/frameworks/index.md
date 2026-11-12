# 框架

- [AscendC](ascendc.md)：AscendC 是昇腾原生 C++ 算子编程框架，提供 Cube、Vector、Scalar 调度、Tiling 和片上缓冲区管理；L2 缓存配置受接口、产品和版本限制。以 DeepSeek-V4 的 SAS、Compressor、LightningIndexer 说明 A3 与 950PR/DT 的实现差异，性能估算方法、对照口径与实测边界见正文。
- [AutoFuse（Inductor NPU 自动融合编译组件）](autofuse.md)：AutoFuse 是面向昇腾 NPU 的 PyTorch Inductor JIT 自动融合组件，将 InductorLoopIR 降为 AscendLoopIR，经 Schedule 模板选择、UB 复用和 ATT 自动 Tiling 后生成 AscendC Kernel。调度以 ComputeType、AxisGroup 和 Merge 规则产生 TilingCase，求解器结合 LocalBuffer、核数、切分与流水耗时选择方案。它主要覆盖 Pointwise/Reduce 等可连续编译区域，避免断图和反复编译；来源文档给出的覆盖口径为 152 个 LoopIR 中 46 个。DeepSeek-V4 的 hc_post 片段在 Atlas A3 典型 shape 下由 30 us 降至 7.5 us（dynamic=False）或 10 us（dynamic=True），但端到端收益尚未验证。AutoFuse 与 GE/npugraph_ex 图后端是并列路径。
- [CANN Executor：统一模型执行与调度](cann_executor.md)：说明当前统一 Executor 的配置、模型/缓存契约、packed 输入、多模态编码和统一 draft 生命周期，撤回旧 runner 分类。
- [KV Cache Manager（框架级 Paged Attention KV Cache 管理）](kv_cache_manager.md)：Executor 分页缓存管理：block_table 将逻辑块映射到物理 block，slot_mapping 指定写入槽位；核对 manager_key、CacheEntry、四种策略、压缩布局、HBM/swapped 分配、容量和 PD 导出。
- [MM Inference Launch（多模态生成模型统一推理拉起架构）](mm_inference_launch.md)：当前四模型YAML启动链、校验/环境优先级、TLS预加载、启动器回退以及缓存/稀疏真实互斥。
- [PyPTO](pypto.md)：PyPTO 以声明式 Tensor 图表达融合算子，经 PTO-ISA、MPMD 调度和后端编译实现不同硬件的适配；本卡维护框架机制，Duration 与 VF 收益由独立观测记录。
- [SGLang](sglang.md)：开源 LLM 推理服务框架，在 cann-recipes-infer 中作为多个模型的基础推理引擎，提供原生的并行能力（TP、EP、DP）和在线推理服务能力。
- [TileLang](tilelang.md)：TileLang当前Ascend适配与分目录、V4 Developer机制和受具体kernel约束的JIT；更新V3.2 LI workspace/布局与安装入口。
- [TorchAir](torchair.md)：当前 TorchAir GE 后端与独立 npugraph_ex 接口、模型特定组合限制、Decode 路由和性能归因边界。

- [在线 PD 分离：控制面、缓存传输与阶段协商](online_pd_inference.md)：在线 PD 分离推理机制：A3 等平台的多机实例、DP 请求分发与 EP 模型前向，Prefill/Decode 控制面协商、逐 CacheEntry 的 KV 传输、投机元数据及资源释放。

- [vLLM Ascend 插件架构：平台、通用注册与多进程初始化](vllm_ascend.md)：解释平台与通用插件注册、Worker与EngineCore补丁的进程安装、VLLM_VERSION版本门控及判断缓存；按真实符号、依赖和初始化时机核对。 对照旧指南核对惰性 ModelRegistry、debug 覆盖和 KV dtype 检查。 补充孤儿 getting_started.po 的插件定位和旧导航边界。 明确旧 Getting Started 的孤儿译文、同路径英文缺失与导航身份。
- [vLLM Ascend ACLGraph：捕获桶、参数更新与重放时序](vllm_ascend_aclgraph_replay_lifecycle.md)：按ACLGraph中英文设计核对wrapper与上游dispatch分工、当前流/更新流顺序和full attention参数刷新，区分地址、指标与正确重放。
- [vLLM Ascend Cohere 音频处理：CPU Mel、长度与处理缓存](vllm_ascend_cohere_audio_processor.md)：按固定原生代码核对 CohereASRFeatureExtractor、FilterbankFeatures 的采样率/形状、dither、精度、逻辑帧与占位token；CPU输入契约不扩展NPU支持。
- [vLLM Ascend CP：虚拟块、请求布局与分片 Attention 合并](vllm_ascend_cp_cache_mapping.md)：依据CP中文设计与原图，解释0 or 1当前写入与历史缓存的区别，区分sparse和request块表范围，核对交织rank、indexer复制与LSE合并。
- [vLLM Ascend 硬件能力契约：HardwareProfile、950DT 与 950PR 产品边界](vllm_ascend_hardware_profiles.md)：说明A2、A3、310P、950的身份、实现族与策略，区分安装表950DT产品声明和950PR待核对边界，沿构建目标、SoC与实际消费者验证能力。 补充孤儿 310p.po 的 DUO、Atlas 200I Pro、event-id 图数量与显式 mask 二次方内存边界。 说明 310P 的 max_model_len、FP16 mask 到 FRACTAL_NZ 的 OOM，2×L² 元素存储与 NZ 转换、512MiB、2GiB、8GiB 原始预算；Eco-Tech W8A8SC 的 8B、14B、32B，DUO 的 triton、triton-ascend 旧卸载，Atlas200IPro 的 root/host page cache 与 HBM，以及 #7394 的 Qwen3.5、Qwen3.6 预览边界。
- [vLLM Ascend 输入元数据：请求索引、位置、块表与 slot mapping](vllm_ascend_input_attention_metadata.md)：按中英文输入示例区分每请求数量与token总数、词表ID/扁平索引/物理块和KV slot，用两轮chunked prefill校验元数据量纲，保留padding与专用路径边界。
- [vLLM Suffix proposer：CPU后缀缓存、变长草稿与Ascend接线](vllm_ascend_suffix_proposer_contract.md)：核对v0.32 SuffixDecodingProposer的Arctic缓存、请求身份、CPU token输入、长度边界和stop_request，区分固定名义K与逐请求变长输出，再检查Ascend工厂和Runner传参。
- [vLLM 模型状态协议：ModelState、专有元数据与采样扩展](vllm_model_state_protocol.md)：沿 ModelState、ModelSpecificAttnMetadata 和 DefaultModelState 区分抽象入口、请求状态、任务列表、自定义采样器与 bonus token，核对 prompt/MM 嵌入的有效行、填充视图及 Ascend 扩展边界。
- [vLLM 多模态输入归一化（Multimodal Input Norm）：参数工厂与后端分派](vllm_multimodal_input_norm_contract.md)：解释 FusedMMInputNorm 的 rescale/mean/std 折叠、processor 配置回退、容差恒等判断、视觉 dtype 转换及 CUDA/XPU/OOT 分派，区分框架数学合同与具体后端执行和性能证据。

- [SGLang 昇腾运行时平台概念](sglang_ascend_runtime/index.md)：说明NPUSRTPlatform的Ascend默认后端、Triton/图能力声明、固定零设备capability和峰值显存口径，区分软件接口与硬件验收。
