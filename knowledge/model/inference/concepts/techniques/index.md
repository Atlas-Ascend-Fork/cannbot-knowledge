# 优化技术

- [Attention-FFN Disaggregation (AFD)](afd.md)：AFD 将 Attention 与 FFN 放在独立节点，通过收发交换中间结果，使两侧计算资源可以分别配置。是否减少等待取决于计算、通信与汇合依赖；该机制本身不保证时延收益。
- [AICPU Scheduler（值依赖分核下沉 ARM 核）](aicpu_scheduler.md)：以当前 SparseFlashMLA/LI metadata 接口说明值依赖分核、压缩长度和余数、CP 模式复用及 Decode 事件同步。
- [CANN SHMEM 通信编程模型](cann_shmem.md)：CANN SHMEM 是面向昇腾多设备的共享地址空间通信模型，以 OpenSHMEM 风格 Host/Device 接口支持跨设备访存和通算融合。它提供 NPU HBM 与 CPU DDR 混合编址、对称内存及 put/get/signal/wait/barrier 等原语；通信域各卡共享虚拟地址，单 die 对称区总量不超过 1 GiB，状态区紧随数据区。基础层使用 MTE/xDMA 处理 D2D/D2H，HIXL 则通过 SDMA 访问远端 DRAM，二者不可混为同一路径。典型用途包括 KV Cache Offload、MoE Dispatch/Combine 和 HIXL 单边通信，可由原生 API、pyPTO 或 TileLang 接入。运行时实现位于外部 cann/shmem 仓，本卡 API 以固定 guide 为依据。
- [DiT 步间缓存：复用、预测与当前模型接入](dit_cache.md)：当前四类DiT缓存、统一YAML、实际模型接入、已修复TeaCache属性及SP/CFG/计数边界。
- [MoE Double-Routing](double_routing.md)：DeepSeek-R1 / Kimi-K2 等大 EP MoE 模型在 Prefill 阶段使用的专家路由方案。每张卡完成 **两轮路由与两轮顺序恢复（末轮调用一次 npu_moe_finalize_routing）**：第一次做本卡内按专家排序 + 通过 AllToAll+ReduceSum 推导 `input_splits` / `output_splits`；token AllToAll 之后再做一次 re-routing 让本卡 token 按本地专家再次排序。相较 AllGather 全量方案，Double-Routing 在负载较均衡时**峰值显存更低**（无数据冗余）且**通信量更小**。
- [HIXL（Huawei Xfer Library 单边零拷贝通信库）](hixl.md)：HIXL 是基于 SHMEM 全局统一编址的昇腾单边通信库，主要解决超长序列推理将 KV Cache 卸载到 CPU DRAM 后的 Device→Remote Host PUT 与 Remote Host→Device GET。它通过 SDMA 直接访问对端 DRAM，无需对端进程参与或内核态中转，并屏蔽 HCCS、RoCE 等链路差异。共享Executor选择Mooncake后端且 protocol=ascend 时调用 HIXL；依赖 libcann_hixl.so、libllm_datadist.so，并需 Mooncake 以 USE_ASCEND_DIRECT 构建。HCCS IPC 缓冲区基址要求 2 MiB 对齐，RoCE 无此约束；默认 memfabric 后端不使用 HIXL。Mooncake 接入行为依据封装代码；HIXL 内部机制依据 guide 文档，未作源码级验证。
- [InferenceConfig（统一推理配置体系）](inference_config.md)：说明当前六类推理配置、独立SpeculativeConfig，以及Decode attention DP与CP Prefill DP的不同公式和token预算，避免沿用旧runner字段。
- [KVCache Offload](kvcache_offload.md)：区分DSA容量型Host卸载与HSTU时序型卸载，说明当前统一CacheEntry、设备workspace预算和offline限制。
- [MoE Dispatch / Combine v2：按模型选择通信与量化](moe_dispatch_combine_v2.md)：更新当前各模型MC2门控、独立组、950量化与fullmesh用法，撤回Gemma旧回退和固定搜索计数。
- [MoE 多流（MoE Multi-Stream）：共享专家旁路与 ScMoE 分支](moe_multi_stream.md)：MoE Multi-Stream 将共享专家与路由专家或 ScMoE 双分支放到多条 NPU stream 并行；解释 Shared + Routed Overlap 与 ScMoE Stream Switch + Core Limit，按对应规则核对条件、同步和回退。
- [MTP Speculative Decoding](mtp_speculative_decoding.md)：解释 MTP 的 draft、主模型验证与接受前缀机制；接入接口、缓存策略和计时指标分别链接规范入口，模型与版本限制不相互外推。
- [NPU 多流机制：资源互补、Stream 与 Event](multi_stream.md)：解释 NPU 资源、流与事件的基本机制及三类并行形态；具体 API、实施步骤、控核和验收分别由规则与指南维护。
- [NPU 图模式（ge_graph / npugraph_ex）](npu_graph_mode.md)：NPU 图模式 ge_graph / npugraph_ex 的执行与编译入口：GE 整图、NpuGraphEx、动态/静态编译、Decode 缓存和后端约束，区分当前接口与旧 ACLGraph tagged API。
- [权重在线切分（Online Split Weight）](online_weight_split.md)：权重在线切分指模型加载时由系统自动将对应权重分发到各个 Device，**无需预先离线处理**，从而避免额外磁盘存储开销、提升调试效率、降低磁盘占用。cann-recipes-infer 在 `module/linear.py`、`module/fuse_moe_gmm.py` 提供了统一的在线切分 Linear / Embedding / MoE GMM 类，并在各模型的 `modeling_*.py` 中通过 `load_weights` 函数做 checkpoint 权重名 → 模型参数名的匹配与分发。 在线切分的核心机制：**每个相关模块在加载权重时获得当前 device 需要加载的权重切片位置**——根据 TP/EP 维度，从原始完整权重中 slice 出本卡分片，直接写入模块参数，跳过全局磁盘中转。
- [Prefill Micro-Batch (Dual-Stream Overlap)](prefill_micro_batch.md)：解释 Prefill 微批次的计算/通信流水与事件依赖；实现步骤和来源性能分别引用 Guide 与观测，不保证所有负载均能获益。
- [Ring Attention Overlap](ring_attention_overlap.md)：当前Ring异步AllGather与本地计算重叠、LSE合并、MXFP8限制及稀疏overlap的独立边界。
- [基于 SHMEM 重写的 MoE Dispatch&Combine](shmem_dispatch_combine.md)：MoE Dispatch 按路由将 token 发往专家所在 rank，Combine 再按逆映射返回并按权重聚合结果。本方案用 CANN SHMEM 对称 win 区和 put/signal/wait 语义，将两者显式编排为发送数据、发送状态、等待状态、本地拷贝四步；Dispatch 还记录来源 rank、token 和 top-k 序号供 Combine 原路返回。guide 给出原生 SHMEM、TileLang-shmem 与 pyPTO-shmem 三种实现，均依赖独立数据区和状态区。它适用于 MoE EP All-to-All 通算融合，但不同于 HCCL double-routing，也不同于将通信封装在 npu_moe_distribute_dispatch_v2/combine_v2 内的融合算子。当前 DeepSeek-V4 生产模型仍调用 torch_npu 融合算子，SHMEM 重写仅为文档级开发示例，未验证独立 cann/shmem 运行时的实际执行行为。
- [SuperKernel](superkernel.md)：SuperKernel 的 scope 调度与融合目标，当前 R1/LongCat 范围差异及通用编译选项和模型限制的边界。
- [weightNZ Format](weight_nz.md)：将 Matmul 类算子的权重 Tensor 转成昇腾 NPU 亲和的 **NZ 分形布局**（512 字节对齐），提升硬件访存带宽效率，加速 DeepSeek-R1 等模型的 Prefill / Decode Matmul 计算。由 YAML `enable_weight_nz: True` 使能，模型加载阶段由 各模块 `quant_method.process_weights_after_loading` 执行 NZ 转换；`convert_model.py` 负责权重量化转换。
- [Weight Prefetch (npu_prefetch)](weight_prefetch.md)：权重预取利用前序计算的带宽窗口提前搬运后续权重，解释缓存与依赖机制；调试规则、LongCat 参数和 AFD 故障入口分别引用规范卡。

- [Packed Sequence：请求边界、长度与 KV 映射](packed_sequence_metadata.md)：区分 packed token、普通长度、累计长度和 slot_mapping，说明 Prefill/Decode 输出及并行通信必须保留请求对应关系。
