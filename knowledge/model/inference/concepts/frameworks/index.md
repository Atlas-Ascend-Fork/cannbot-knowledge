# 框架

- [AscendC](ascendc.md)：AscendC 是昇腾原生 C++ 算子编程框架，提供 Cube、Vector、Scalar 调度、Tiling 和片上缓冲区管理；L2 缓存配置受接口、产品和版本限制。以 DeepSeek-V4 的 SAS、Compressor、LightningIndexer 说明 A3 与 950PR/DT 的实现差异，性能估算方法、对照口径与实测边界见正文。
- [AutoFuse（Inductor NPU 自动融合编译组件）](autofuse.md)：AutoFuse 是面向昇腾 NPU 的 PyTorch Inductor JIT 自动融合组件，将 InductorLoopIR 降为 AscendLoopIR，经 Schedule 模板选择、UB 复用和 ATT 自动 Tiling 后生成 AscendC Kernel。调度以 ComputeType、AxisGroup 和 Merge 规则产生 TilingCase，求解器结合 LocalBuffer、核数、切分与流水耗时选择方案。它主要覆盖 Pointwise/Reduce 等可连续编译区域，避免断图和反复编译；来源文档给出的覆盖口径为 152 个 LoopIR 中 46 个。DeepSeek-V4 的 hc_post 片段在 Atlas A3 典型 shape 下由 30 us 降至 7.5 us（dynamic=False）或 10 us（dynamic=True），但端到端收益尚未验证。AutoFuse 与 GE/npugraph_ex 图后端是并列路径。
- [CANN Executor：统一模型执行与调度](cann_executor.md)：说明当前统一 Executor 的配置、模型/缓存契约、packed 输入、多模态编码和统一 draft 生命周期，撤回旧 runner 分类。
- [KV Cache Manager（框架级 Paged Attention KV Cache 管理）](kv_cache_manager.md)：Executor 缓存管理的四种策略、manager_key 分组、压缩布局、HBM 与 swapped 分配、owner 选择、投机状态预留及 PD 导出限制；按当前实现核对容量公式与接入契约。
- [MM Inference Launch（多模态生成模型统一推理拉起架构）](mm_inference_launch.md)：当前四模型YAML启动链、校验/环境优先级、TLS预加载、启动器回退以及缓存/稀疏真实互斥。
- [PyPTO](pypto.md)：PyPTO 以声明式 Tensor 图表达融合算子，经 PTO-ISA、MPMD 调度和后端编译实现不同硬件的适配；本卡维护框架机制，Duration 与 VF 收益由独立观测记录。
- [SGLang](sglang.md)：开源 LLM 推理服务框架，在 cann-recipes-infer 中作为多个模型的基础推理引擎，提供原生的并行能力（TP、EP、DP）和在线推理服务能力。
- [TileLang](tilelang.md)：TileLang当前Ascend适配与分目录、V4 Developer机制和受具体kernel约束的JIT；更新V3.2 LI workspace/布局与安装入口。
- [TorchAir](torchair.md)：当前 TorchAir GE 后端与独立 npugraph_ex 接口、模型特定组合限制、Decode 路由和性能归因边界。

- [在线 PD 分离：控制面、缓存传输与阶段协商](online_pd_inference.md)：在线 PD 分离推理机制：A3 等平台的多机实例、DP 请求分发与 EP 模型前向，Prefill/Decode 控制面协商、逐 CacheEntry 的 KV 传输、投机元数据及资源释放。
