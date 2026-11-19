# 模型推理指南

按任务选择实施、验收与回退流程。

- [模型跑通指南](bringup/index.md)：当前Sana导入兼容补丁、必传quant_type的方法注入时序、加载后权重同步与量化替换。
- [模型部署指南](deployment/index.md)：共 40 张知识卡（如 已停用：LongCat A3 长序列 KVP 的历史条件与配置、推理并行配置选型：按 Prefill、Decode 和模型结构找参考 YAML、量化部署：先检查权重格式，再选转换或直载 等）。
- [模型集成指南](integration/index.md)：共 321 张知识卡（如 Attention 融合链选型：GQA、MLA Absorb 与 Indexer 稀疏路径、块稀疏 Attention 与 Ulysses 序列并行同时使能（看全序列 + 规范序重映射 + head 负载均衡）、compressed-tensors 接入：产物契约、targets/ignore 与运行加载链 等）。
- [模型优化指南](optimization/index.md)：共 40 张知识卡（如 LLM Decode 图模式：编译配置、backend 定界与精度排查、kernel_details 字段解读：流水指标、控核与多流真实重叠、多流优化流程：拆解依赖、选择后端并验收真实收益 等）。
- [模型专用指南](models/index.md)：共 44 张知识卡（如 DeepSeek-R1 A3 分阶段部署与优化验收流程、DeepSeek-V3.2-Exp A3 长序列部署与验收流程、DeepSeek V4.1 Flash：950 单卡的 Engram 与专家卸载 等）。

- [SGLang 昇腾模型、量化与适配指南](sglang_ascend/index.md)：共 38 张知识卡（如 SGLang 昇腾 LoRA 的驻留槽、逐 rank 一致性与安全清零、SGLang 昇腾 LoRA 的 SGEMV、批次元数据与图边界、SGLang 昇腾模型默认后端与量化配置守卫 等）。
- [模型推理验证与测试](testing/index.md)：共 22 张知识卡，分布在 1 个子目录（sglang_ascend）。
- [FIA KV 伪量化：版本、阶段与 scale 布局矩阵](fia_kv_antiquant_modes.md)：对照主线 v1/v2 的 KV 分离模式、打包 INT4/FP4、PagedAttention 与 GQA NZ 条件，保留产品差异。
- [FIA mask、共享前缀与 LSE：窗口语义和占位边界](fia_mask_prefix_and_lse.md)：区分sparse模式、行无效修正、v1前缀/左padding、950差异及主线真实输出占位，避免错误复用示例。
- [FIA MLA 与 packed 布局：RoPE、累计长度和输出轴](fia_mla_and_packed_layouts.md)：按主线产品及D=128/512分开核对TND/NTD、分页长度、独立RoPE、Sink与布局文档冲突。
- [FIA 全量化：INT8、MXFP8 与 GQA FP8 的执行边界](fia_quantized_attention_paths.md)：区分主线量化参数组、950模式三元组、scale物理形状和Eager限定，记录文档冲突与不可推断项。
- [发布AttentionPioneer：外部workspace、out复用与准备期分配](torch_npu_attention_pioneer_workspace_and_out.md)：核对内部Pioneer的普通/out/max-workspace/infer-output路径，区分字节与元素计数、storage基址及仍存在的执行准备成本。
- [ATB分页注意力执行：描述符、Operation缓存与工作区](torch_npu_atb_paged_attention_execution_lifecycle.md)：沿PA和MLA入口核对完整bridge类型转换、输入准备、Operation缓存、捕获分派、Setup及显式工作区边界。
- [ATB MLA准备：固定输出、Cache格式与Ring统计](torch_npu_atb_mla_preprocess_and_ring_preparation.md)：聚合MLA预处理和Ring MLA的输出分配、模式默认值、CPU长度要求与执行宏消费者，区分Cache输出和输入别名。
- [ATB分页变体准备：长度列表、掩码与SplitFuse](torch_npu_atb_paged_attention_v2_and_splitfuse_preparation.md)：对照分页V2和SplitFuse的长度、掩码、格式和工作区准备，并绑定固定ATB参数头文件的枚举、默认值与条件。
- [ATB量化分页注意力：反量化输入与输出准备](torch_npu_atb_quantized_paged_attention_preparation.md)：核对量化PA的注册、参数类型、反量化槽和caller out，并纳入固定PagedAttentionParam头文件的dtype、形状及组合约束。
- [ATB FlashAttention族：掩码、长度与内核模式](torch_npu_atb_flash_attention_family_preparation.md)：聚合普通、V2、V3与unpad入口，连接固定SelfAttention参数、掩码装填、格式准备和Operation缓存，保留文档及版本差异。
- [ATB分组路由：GroupTopk参数、原地输出与测试边界](torch_npu_atb_group_topk_routing_and_alias.md)：记录分组打分模式、整数窄化、固定索引输入、schema与原地输出差别，以及已跳过参考测试的实际范围。
- [ATB矩阵累加：转置配置、FP32 C与输入连续化](torch_npu_atb_matmul_add_fp32_accumulation.md)：沿MatmulAddFP32核对固定转置和无bias累加、C输入输出别名、厂商局部条件及非连续矩阵测试的范围。
- [ATB前缀注意力：双长度、压缩掩码与输出准备](torch_npu_atb_prefix_attention_lengths_masks_and_outputs.md)：对照Prefix V2、qlens和PrefixEncoder三条准确入口，区分Q/KV长度、SelfAttentionParam与动态宏、掩码分支、Meta和测试证据范围。
- [ATB量化输入准备：RMSNorm与Tensor量化](torch_npu_atb_quant_rmsnorm_and_tensor_quantization.md)：区分两条量化入口的固定参数、Tensor scale/offset、格式与输出合同，并记录测试参考、捕获范围和固定版本差异。
- [ATB KV Cache写读：槽位、NZ配置、长度与输出](torch_npu_atb_kv_cache_write_and_paged_read_preparation.md)：聚合双Cache/SISO写入与分页读取，区分两套格式模式数字、长度校验和out路线，并保存完整测试中的参考与别名边界。
- [ATB RoPE：静态cos/sin缓存、长度失效与原地输出](torch_npu_atb_rope_static_cache_and_inplace_preparation.md)：分开记录位置编码表和Operation缓存、两种排布、只按token数更新的长度状态，以及aot_eager测试的真实范围。
- [ATB专家路由：FusedAddTopkDiv参数、映射与测试边界](torch_npu_atb_fused_add_topk_div_routing.md)：固定普通/out路由接口及14实参，核对专家映射文档冲突、Meta与被跳过完整测试的实际参考和比较范围。
- [ATB MLA分页注意力：LSE、工作区与图更新合同](torch_npu_atb_mla_lse_workspace_and_graph_update.md)：聚合五个MLA schema、18实参和LSE/工作区分支，区分Meta与设备输出、文档类型冲突及完整图更新测试边界。
- [AFD ScheduleContext 生产侧：1024字节上下文、窗口布局与停止语义](torch_npu_afd_schedule_context_holder_mechanism.md)：记录 torch_npu._afd 调度上下文 holder 的参数门槛、FFN/Attention 窗口切分、设备副本与 stop_schedule 机制；两版均在、接线不同，仓内无业务调用方。
- [FFN Worker上下文：测试打包、缓冲持有与参考验收边界](torch_npu_ffn_worker_context_and_reference_limits.md)：补齐FFN Worker测试的packed上下文、偏移与设备地址、随机参考及仅断言y的范围，复用既有八返回和调度隔离合同。
- [TorchNPU原生量化Tensor的表示、存储与版本派发](torch_npu_native_quantized_tensor_storage_and_dispatch.md)：说明原生per-tensor/per-channel的版本分支、整数承载、PrivateUse1回调、元数据与反量化成本。
