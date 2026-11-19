# 指南

- [实践指南](recipes/index.md)：共 13 张知识卡（如 DeepSeek-R1 veRL + MindSpeed + vLLM-Ascend 全共卡 GRPO RL 训练、DeepSeek-V3.2 当前训练配置与 32K 优化案例、DeepSeek-V3 裁剪模型 MXFP8/HiF8 低精度预训练（MindSpeed · Atlas 950 950DT · 8K） 等）。

- [TorchNPU 训练通信内存复用：Work.wait 与引用寿命](torch_npu_collective_memory_reuse.md)：说明 MULTI_STREAM_MEMORY_REUSE 各模式、主线默认2与发布默认1的差异及解析行为，模式2下异步集合通信必须 Work.wait；核对 Work.wait 的当前流等待语义、非阻塞返回含义、引用保护与标记擦除的释放时机，并区分引用保护与业务同步。

- [TorchNPU DDP 与 FSDP2：基础接入和配套核验](torch_npu_ddp_fsdp_adaptation.md)：限定固定主线 PyTorch2.14 清单中的 A2/A3与950DT 基础 DDP/FSDP2 接入，说明输入精度、全局 rank 和复杂组合边界。
- [TorchNPU pg_options：按通信域配置 HCCL](torch_npu_hccl_pg_options.md)：说明 hccl_config 名称映射、优先级、不继承规则及创建后不可重配边界。

- [RankTable 建链：文件选择、回退与错误配置](torch_npu_ranktable_communication_init.md)：说明全局域及子域建链、文件缺失与内容错误的不同结果，区分初始化与稳态通信。
- [Scalable RootInfo：按 ProcessGroup 分级建链与回退边界](torch_npu_scalable_rootinfo.md)：说明 root 数和均衡分组、A2/A3 及 HCCL 接口要求，区分 RankTable 和 TCPStore 分层。

- [TorchNPU Autocast：精度上下文与自定义前反向迁移](torch_npu_autocast_and_custom_autograd.md)：按 PyTorch2.14 清单与实现区分 autocast、GradScaler 和自定义装饰器，保留旧入口弃用边界。
- [TorchNPU 融合优化器：组合存储、梯度清零与裁剪](torch_npu_fused_optimizer_lifecycle.md)：解释融合优化器基类的首次组合、FP16/FP32 两槽、组合缓存与分组偏移、闭包次序、清零和带掩码裁剪的确切前提，区分张量融合与低精度/分片优化器。
- [TorchNPU GradScaler：反缩放、溢出与更新状态机](torch_npu_grad_scaler_contract.md)：区分动态与静态缩放、每优化器调用顺序及普通/融合梯度路径，避免把跳步当成参数已更新。

- [TorchNPU 通信内存：P2P 缓冲、零拷贝与对称堆](torch_npu_communication_buffers_and_zero_copy.md)：区分每通信域独占的 P2P 缓冲、实验零拷贝和 NPUSHMEM 对称堆，不与计算缓存分配器混算。
- [TorchNPU Inf/NaN：计算模式与溢出检测分开配置](torch_npu_inf_nan_and_overflow_detection.md)：区分饱和模式改变数值、非饱和模式检测与 950 的查询限制，说明 FORCE_OVERFLOW_CHECK 的 CANN 门槛。
- [原生集合通信 NPU 清单：dtype、迁移映射与兼容路线](torch_npu_native_collective_constraints.md)：按 PyTorch2.14 的逐 API 限制区分点对点、归约、Gather 和 AllToAll，不由通用 HCCL 可用推导所有 dtype。
- [原生优化器 NPU 路线：foreach、fused 与 dtype 清单](torch_npu_native_optimizer_modes.md)：说明参数分组对 foreach 的影响、Adam/AdamW/SGD 的不同限制及类与方法 dtype 表述冲突。
- [TorchNPU 精度开关：HF32 与确定性内存填充](torch_npu_precision_switches_and_deterministic_fill.md)：说明 CUDA allow_tf32 兼容属性不保证生效，区分 NPU HF32 运算策略与未初始化内存填充。

- [词表并行融合损失：局部参考点、通信和反向交付](torch_npu_vocab_parallel_loss_contract.md)：串联三个显式接口，推导局部最大值不同为何不能直接相加 exp 和，并保留词表边界与产品交集。

- [Lightning Indexer训练的稠密与稀疏阶段契约](torch_npu_lightning_indexer_training_contract.md)：分开warmup稠密统计与稀疏KL路径，避免交换teacher/Indexer归一化信息或推导端到端图支持。

- [原生激活重计算的版本、dtype与产品边界](torch_npu_native_checkpoint_boundaries.md)：说明checkpoint_sequential的FP32支持表范围，避免推广到全部checkpoint或把未列950条目当绝对禁止。
- [原生数据加载的NPU多进程限制与dtype清单边界](torch_npu_native_data_loading.md)：说明固定版本DataLoader对NPU数据的限制，区分CPU加载、目录dtype措辞及Prefetcher流复用。
- [原生张量并行的dtype与950损失精度边界](torch_npu_native_tensor_parallel_constraints.md)：说明ColwiseParallel和loss_parallel支持表条件，区分整数输入名单与logits类型、模块布局和产品遗漏。

- [DDP 通信钩子：压缩输入、PowerSGD 与产品范围](torch_npu_ddp_communication_hooks.md)：记录七个原生版本页中的 FP32 限制与 950DT 支持差异，区分 hook、wrapper 和端到端收益。
- [确定性算法范围：产品清单与主线状态冲突](torch_npu_deterministic_algorithm_scope.md)：区分 A2/A3 与 950DT 的算子清单、布尔状态和真实下发，不从总览推导统一的一次设置限制。

- [原生卷积NPU迁移：dtype、内部格式与950数值边界](torch_npu_native_convolution_constraints.md)：区分Conv/Lazy/functional支持表、A2内部格式编译条件、950DT卷积W上限及cube枚举配置。
- [原生归一化NPU边界：AMP、反向与兼容实现](torch_npu_native_normalization_constraints.md)：对比BatchNorm、GroupNorm类与functional的dtype、rank、eps和反向限制，明确LayerNorm内存一致性选择。
- [原生RNN的NPU限制：变长、投影与编译路径](torch_npu_native_recurrent_constraints.md)：区分LSTM、GRU及Cell的公开范围，记录LSTMCell黑名单文字与DynamicRNNV2实现不一致及950未核对项。
- [NPU重采样与像素重排：尺寸、dtype和CPU回退](torch_npu_native_vision_resampling.md)：区分interpolate/旧upsample入口的参数与950DT double边界，以及PixelShuffle类函数差异和可能的Host计算。并含 Nearest-exact 1D 前后向：尺寸推导借用linear1d helper、同构DO_COMPATIBILITY往返与SymInt声明差异。并含普通 upsample 七族：双层回退结构、尺寸helper不对称与scale缺省值分裂；含普通七族 acl_op 回退内部：ACE 命令、dtype cast 与 scale 处理分裂。并含 网格采样与affine网格：grid_sampler 生成层登记、Half 往返分裂与 affine 反向的 BatchMatMul 组合。

- [原生Embedding与Linear：索引、权重和精度边界](torch_npu_native_embedding_linear_constraints.md)：分开Embedding的input/weight及子方法限制、Linear类函数dtype差异与950DT精度开关，避免误读参数表。并含 embedding_renorm_ 双路维护路径。
- [原生损失的NPU边界：标签、梯度与文档版本](torch_npu_native_loss_constraints.md)：对照标签边界、梯度回流与文档版本差异，保留MultiMargin/CTC/多标签的类型表。并含 KL/BCE/L1/SoftMargin 的生成直发规格与反向接线。并含 multi_margin_loss 的负向确认：主线与发布两版本 yaml 与源树均无注册/实现，文档表支持不能由来源源码认证。并含BCEWithLogits aclops 回退与 custom 反向实现层。
- [原生Padding的NPU限制：模式、dtype与高维开销](torch_npu_native_padding_constraints.md)：区分constant/非constant及具体Pad类的支持表，保留文档差异、高维性能提示与ZeroPad2d CPU回退；含 Reflection/Replication/Constant Pad 的 Eager 包装层：生成命令、FP4/高维边界与 acl_op 回退内部；含 reflection/replication_pad3d 生成层 wrapper 实际行为：无 DO_COMPATIBILITY 的直发合同与 4D/5D 尺寸 helper。并含 constant_pad_nd 的FP4/FP8测试合同：主线FP8(e4m3fn/e5m2) pad支持面、950门控与主线与发布两版本测试内容差。
- [原生池化NPU契约：索引、反池化与版本差异](torch_npu_native_pooling_and_indices.md)：按版本区分950DT AvgPool3d支持，核对MaxPool的dilation、INT32索引、兼容实现及类函数dtype差异；含 AvgPool/MaxPool/AdaptivePool 的 Eager 包装层：双命令路由、indices 三形态与 acl_op 回退内部。并含 im2col/col2im：SoC 门、空输出短路的 pin 差与 ND→NCHW 桥。

- [原生激活函数的NPU边界：近似算法、dtype与反向](torch_npu_native_activation_precision.md)：对照GELU近似和兼容路径、SELU FP16梯度、Threshold大整数，以及SiLU等类函数和文档版本差异。并含 _add_relu 生成直发 aclnn 与两命令 acl_op 回退。并含 ELU/CELU、GLU、LeakyReLU 三子族的生成直发、acl_op 回退与 dtype/门槛不对称。并含 Hard* 五子族、Mish/Softplus/LogSigmoid 的手写 opapi 与回退差异，以及原地变体与 PReLU 的申请依据、RNG 来源和回退形态。
- [原生Dropout的NPU范围：类函数差异与950复数限制](torch_npu_native_dropout_scope.md)：区分Dropout各入口dtype与950DT的complex例外，不从随机算子注册推定训练、捕获或零拷贝支持。并含 native_dropout_backward 的scale合同、p==0/p==1分支与主线950 aclnnDropoutV3Grad原始scale直发路及打包位掩码协议。

- [原生注意力模块的NPU范围：MHA与Transformer层级](torch_npu_native_attention_modules.md)：区分MHA、Transformer与Encoder.forward的dtype清单、950DT精度提示及独立SDPA/图模式边界。
- [原生scaled矩阵乘的NPU模式：ScalingType与文档边界](torch_npu_native_scaled_matrix_modes.md)：区分scaled_mm和scaled_grouped_mm的FP8/MX模式、A2/A3产品表及委托scale形状，不按其他量化API外推。并含 主线950包装层输入合同：_scaled_mm/_scaled_grouped_mm及v2的SoC门、FP8 dtype/scale/bias/scale_result/out_dtype与NZ/V5符号可用性检查。

- [原生距离函数：950DT与文档版本的支持差异](torch_npu_native_distance_functions.md)：区分PairwiseDistance类和functional、pdist的版本标记以及cosine_similarity的输入类型；含 cdist/pdist 家族 Eager 实现层：p 的 inf 哨兵分裂、_pdist_backward 的 CPU triu 索引桥与 cdist 反向复用、_cdist_backward 主线三层门与发布恒门的 pin 差。
- [原生梯度工具：裁剪、范数与向量化dtype范围](torch_npu_native_gradient_utilities.md)：区分clip_grad_norm/value的类型表、辅助范数接口和参数向量数据角色，不替代融合优化器专用协议。
- [原生Module与参数容器：方法级平台和dtype边界](torch_npu_native_module_and_container_scope.md)：区分Module.compile/double等950DT例外、方法类型表、Parameter/Buffer与Lazy元数据，避免泛化到所有模型参数。
- [原生剪枝与参数化：方法限制和950DT差异](torch_npu_native_pruning_and_parametrization.md)：区分随机剪枝类与函数的产品表、mask和weight数据角色、参数化正交入口与真实稀疏执行边界。并含 aten::_weight_norm 本地包装的同设备守卫与纯 aten 组合。

- [原生FFT：环境依赖、rfftn尺寸与950DT限制](torch_npu_native_fft_constraints.md)：保存ATB/ASDSIP环境要求、rfftn输入数值与长度条件，以及ifftshift的950DT类型排除；含FFT计划缓存（FFTMixCache容量与淘汰）、系数矩阵生成与ASDSIP ABI层（libasdsip.so句柄生命周期与MKI描述符）。
- [原生参数初始化：FP32清单与950DT例外](torch_npu_native_initialization_constraints.md)：区分nn.init的类型、trunc_normal_与sparse_产品边界，避免用legacy随机实现名单覆盖接口支持。
- [原生线性代数：分解精度、LU产品与CPU回退](torch_npu_native_linalg_constraints.md)：区分linalg接口的输入类型、六维matmul限制、lu的950DT范围和lstsq可能回退CPU。并含 linalg_cholesky/qr/cross 的符号探测回退、本地检查与旧ACL整备。并含 trace 与 triangular_solve.X 的对角和、双输出三角求解包装。
- [原生特殊函数：类型表与multigammaln定义域](torch_npu_native_special_functions.md)：区分erf/erfc、整数及复数输入条目，保留multigammaln的正整数p和输入域限制。

- [原生自动微分：反向、前向与函数变换边界](torch_npu_native_autograd_transforms.md)：区分backward稀疏排除、FP32高阶入口、jvp命名空间差异及950DT子方法限制。
- [原生稀疏与嵌套Tensor：构造、子方法和反向边界](torch_npu_native_sparse_nested_scope.md)：保留稀疏压缩入口的950DT差异，以及嵌套张量“仅创建”文字与转换操作表的张力。并含 _coalesce 宿主组合链与 to_padded_tensor 原生委托的实现层；含 add.out/mul.out 的 sparse 标记实现层：index_add/cat 组合链与 mul 的 dense 往返。

- [原生分布式检查点：保存、Planner与Stager产品边界](torch_npu_native_distributed_checkpoint_scope.md)：区分DCP公开保存入口、状态转换和子方法范围，保留DefaultStager的950DT未验证标记与版本缺项。
- [原生分布式优化器与Join：融合对象和950DT子方法限制](torch_npu_native_distributed_optimizer_join.md)：保留ZeroRedundancyOptimizer的输入对象限制及Join/状态/更新方法差异，不从类表推出全流程可用。
- [原生弹性训练：Agent、Rendezvous与启动范围](torch_npu_native_elastic_scope.md)：区分Agent和后端组件支持，保留torchrun条目、etcd、健康检查与日志子项的950DT限制。
- [原生RPC与Future：NPU后端适配和完成边界](torch_npu_native_rpc_future_scope.md)：说明NPU_TENSORPIPE及NPUTensorPipeRpcBackendOptions要求，区分Future、远程模块与分布式优化器支持。
- [原生学习率调度与参数平均：方法类型和产品边界](torch_npu_native_scheduler_averaging_scope.md)：区分lr与参数dtype，保留MultiplicativeLR状态保存的950DT排除及SWA/EMA中文清单范围。

- [原生概率分布：采样、CPU回退和950DT方法边界](torch_npu_native_distribution_scope.md)：区分分布类与采样/统计子项，整理CPU回退、随机行为、协方差维度和变换约束。
- [原生量化与QAT：准备、转换和模块产品边界](torch_npu_native_quantization_scope.md)：整理TorchAO配置/Observer/FakeQuantize与量化模块的独立支持表，保留950DT和旧数值对照工具差异；补主线量化flip源码门槛与构建期接线边界。并含 q_* 量化张量描述符与 quantize_per_tensor/per_channel 的 op-plugin 双派发路实现。

- [Tensor索引与归约：重复索引、排序及CPU回退](torch_npu_native_tensor_index_reduce_scope.md)：保留方法级dtype和版本变化，记录950排序稳定性、scatter_reduce加速条件及数值边界。
- [Tensor数学方法：dtype、950精度与CPU回退](torch_npu_native_tensor_math_scope.md)：按Tensor方法与原地变体分别记录运算类型、矩阵乘版本差异和可能回退CPU的入口。
- [Tensor随机方法：950行为、类型与CPU回退](torch_npu_native_tensor_random_scope.md)：区分Tensor原地随机填充和概率分布类，保留BOOL迁移建议与950产品局部说明。

- [torch索引与统计：函数级类型和排序条件](torch_npu_native_torch_index_reduce_scope.md)：记录重复索引、isin单双Tensor、统计归约、950稳定排序及CPU回退限制。并含 cummax/cummin helper 的 aclnn 直发、kLong 分叉与 INT32 索引路径。
- [torch逐点与foreach运算：函数级类型和数值限制](torch_npu_native_torch_math_scope.md)：核对torch数学函数及foreach条目的局部类型、广播、输出dtype和可能CPU回退条件。
- [torch矩阵与信号运算：精度模式、距离和形状限制](torch_npu_native_torch_matrix_signal_scope.md)：核对函数级矩阵乘类型、950精度代价、cdist模式、STFT迁移及窗口误差范围；含 BLAS 向量入口 addmv/addr/dot/mv/vdot 的 Eager 包装层：dtype 参照分裂、acl_op 组合命令与生成层 exec 合同。

- [torch_npu_run：启动器分层TCPStore与通信域分层的区别](torch_npu_run_tiered_tcpstore.md)：整理大集群启动参数和proxy连接结构，区分rendezvous与HCCL后端；缺少完整产品矩阵，保留草稿。

- [MNIST自动迁移验收：设备替换、AMP与检查点边界](torch_npu_mnist_migration_acceptance.md)：以固定A2教程区分transfer_to_npu映射、前反向精度步骤及本卡检查点证据，避免把训练结束当识别效果或性能验收。

- [LLM微调基准复核：数据身份、参数转发和计时回调](torch_npu_llm_benchmark_inputs_and_switches.md)：保存九个模型教程的实际入口与样例差异，区分请求的LoRA/精度/编译配置和当前脚本真正接收的参数。
- [SimpleV1SparseDrive示例：随机负载、局部编译与训练计时](torch_npu_simple_sparsedrive_benchmark.md)：区分简化SparseDrive工作负载和真实任务验收，记录仅编译backbone、eager也应用分解补丁以及计时未覆盖同步的边界。

- [发布快照数学与量化清单：配置支持和执行缺口](torch_npu_release_native_math_quantization.md)：保留量化配置/Observer的Y与量化转换/算子空白，限定linalg和special短名单。
- [发布快照NN清单：模块、functional与初始化差异](torch_npu_release_native_nn_contracts.md)：保留Module及functional独立兼容状态、激活dtype短名单和未验证卷积/SDPA等条目。
- [发布快照训练清单：通信、FSDP、优化器与重计算](torch_npu_release_native_training_contracts.md)：区分类/方法级Y与空白，保留FP16与BF16通信钩子差异及未验证弹性、TP和DCP表。

- [TorchNPU矩阵乘执行路径：NZ分派、精度透传与反向搬运](torch_npu_matmul_execution_paths.md)：定位OpPlugin原生matmul的格式和符号门槛、显式CubeMathType优先级，以及广播反向的布局处理和版本差异。

- [TorchNPU FSDP2 增强入口：通信缓冲复用与重计算钩子](torch_npu_fsdp_enhance_memory_and_recompute_hooks.md)：区分增强 fully_shard 入口、私有缓存标志、两版通信分配接口及 post-forward 状态，解释缓存释放为何不等于显存归还。
- [SwiGLU双轴MX前反向：结果配对、FP4承载与梯度边界](torch_npu_swiglu_dual_axis_training_contract.md)：补齐SwiGLU双轴MX显式前反向的四返回、E8M0尺度容量和FP4物理形状，区分前向偶数与反向64对齐。

- [SwiGLU Group Quant训练接入：默认模式、占位输出与自动求导](torch_npu_swiglu_group_quant_training_contract.md)：核对OpPlugin Group Quant仅mode2/3的HiF8分配、忽略的dst_type、Meta空值分歧及grads[2]自动求导依赖。

- [原生卷积执行：路由、梯度分配与格式成本](torch_npu_convolution_execution_paths.md)：核对OpAPI与旧ACL卷积路由、mask仍分配的梯度、FP32权重梯度中间值、格式与contiguous成本及HF32重载。

- [原生融合Adam执行：CPU回退、分批与AMP参数边界](torch_npu_native_fused_adam_execution.md)：区分原生Adam的CPU回退/512项批处理与AdamW逐参数调用、临时状态、学习率读取及局部未消费AMP参数。

- [原生融合SGD：溢出跳过、设备检查与Host标量](torch_npu_native_fused_sgd_execution.md)：区分scalar/tensor_lr重载的found_inf检查顺序、正动量、设备条件与item读取，限定原生列表更新及AMP接入边界。

- [原生AMP反缩放：分批、溢出状态与更新入口](torch_npu_native_amp_unscale_execution.md)：核对原生AMP的250 Tensor分批、状态读取与原地写入，并区分TorchNPU GradScaler的实际scale更新消费者。

- [原生LayerNorm执行：统计精度、掩码分配与兼容分派](torch_npu_native_layer_norm_execution.md)：核对原生LayerNorm的版本门控、空batch统计shape、反向FP32仿射梯度与ACL回退掩码差异，区分公开限制和实际包装。

- [原生BatchNorm的OpAPI：统计输出、补写与掩码分配](torch_npu_native_batch_norm_opapi_execution.md)：区分主线与发布的训练/推理统计输出、out引用和重叠保护，核对BatchNorm反向掩码及FP32仿射梯度申请。

- [原生GroupNorm桥接：统计对象、反向掩码与分派边界](torch_npu_native_group_norm_batch_norm_bridge.md)：追踪GroupNorm到ATen BatchNorm反向的对象与槽位，区分前向统计、候选分派、掩码分配和无条件view的静态边界。

- [原生EmbeddingBag：辅助缓冲与CPU反向搬运](torch_npu_embedding_bag_aux_buffers_and_cpu_backward.md)：核对EmbeddingBag四输出的SoC分支、ACL空输入与索引转换，以及per-sample weights反向的整表CPU复制请求。
- [原生Embedding稠密梯度：整表分配与索引宽度](torch_npu_embedding_dense_gradient_allocation.md)：区分Embedding稠密反向的整表输出、ACL索引INT32转换与OpAPI生成声明，避免从前向或稀疏参数外推梯度能力。

- [原生NLLLoss执行：权重轴、标量统计与out准备](torch_npu_nll_loss_output_and_backward_execution.md)：区分普通及2D NLLLoss的缺省权重、前反向分配和out检查，保留标签、dtype与底层数学未核对边界。

- [原生GELU反向：类型准备、近似校验与版本路由](torch_npu_gelu_backward_precision_and_routing.md)：追踪GELU反向的广播和result_type输出准备、近似字符串校验顺序，以及ACLNN-only与兼容标志的两版差异。
- [原生Softmax执行：升精度、out整理与反向分配](torch_npu_softmax_dtype_and_output_execution.md)：区分Softmax及LogSoftmax的ACL分配和输入转换，核对out格式回写、input_dtype边界与两版生成声明差异。并含 aten::_masked_scale 生成直发aclnnMaskedScale的注册与包装边界。

- [索引累加执行：初值复制、连续克隆与out差异](torch_npu_indexed_add_buffer_preparation.md)：核对index_add与scatter_add在OpAPI中的初值准备、原地与out边界及版本检查差异，避免遗漏复制和连续化开销。

- [TorchNPU 私有 DistributedMuon：三路正交化与分布式边界](torch_npu_distributed_muon_execution.md)：依据主线完整本地模块梳理 BF16 Newton–Schulz、Shard 分派、通信、动量和学习率缩放，保留进程组与 DTensor 适用条件。
- [TorchNPU Adam 家族：组合状态、投影、预热调度与信任比](torch_npu_fused_adam_family_execution.md)：完整对照 Adam、AdamW、AdamP、BertAdam、Lamb 的双版本本地实现，区分状态计步、权重衰减、裁剪和辅助缓冲。
- [TorchNPU SGD、Adadelta 与 RMSprop：首步状态和更新差异](torch_npu_fused_classical_optimizer_execution.md)：完整核对双版本四个优化器的状态恢复、组合计步、动量与 epsilon 位置，保留 RMSpropTF 衰减和旧组字段的源码语义。

- [TorchNPU AMP原生注册：版本策略、状态桥接与脚本分支](torch_npu_native_autocast_registration_and_script_branches.md)：对照两版Autocast注册、四个PrivateUse1状态方法与完整Python包装，核对脚本分支和私有容器cast边界。

- [融合AddLayerNorm：残差输出、梯度复用与Meta边界](torch_npu_add_layer_norm_residual_gradients_and_meta_boundaries.md)：记录AddLayerNorm前后向的混合dtype分配、统计shape、optional梯度补零和双槽dx句柄复用，说明Meta差异及跳过测试的边界。
- [all/any布尔归约：Byte直传、兼容回退与不对称整理](torch_npu_all_any_bool_reduction_routes.md)：区分all/any的aclnn直发与ReduceAll/ReduceAny回退、Byte/Bool输出dtype与空输入分支，并记录两派发路输出dtype可观察差异。
- [批量P2P的派发与Work列表：版本门槛和子组rank](torch_npu_batched_p2p_route_and_request_contracts.md)：对照两版P2P的coalescing/backend批派发、Work数量、组内rank及debug包装门槛。
- [拼接与拆分复制：空输入、布局和融合门控](torch_npu_cat_chunk_and_split_copy_execution.md)：对照Cat的空张量过滤与主线Dimname守卫、ChunkCat的SoC与dtype快路，以及SplitWithSizesCopy两代融合门和主线新增本地检查。
- [TorchNPU上下文并行的注册作用域与序列策略](torch_npu_context_parallel_dispatcher_scope.md)：TorchNPU上下文并行的注册作用域与序列策略的本地规则、适用条件及未核对外部边界。
- [TorchNPU上下文并行的Ring Attention与Softmax状态](torch_npu_context_parallel_ring_softmax_state.md)：TorchNPU上下文并行的Ring Attention与Softmax状态的本地规则、适用条件及未核对外部边界。
- [TorchNPU DTensor AdamW out状态布局与对象复用](torch_npu_dtensor_adamw_out_state_layout.md)：TorchNPU DTensor AdamW out状态布局与对象复用的固定双版本本地规则、重分布边界与验收条件。
- [TorchNPU DTensor通信Matmul的布局和全局Meta修正](torch_npu_dtensor_comm_matmul_global_metadata.md)：TorchNPU DTensor通信Matmul的布局和全局Meta修正的固定双版本本地规则、重分布边界与验收条件。
- [TorchNPU DTensor卷积与分组原地累加布局](torch_npu_dtensor_conv_and_grouped_accumulation.md)：说明卷积batch和输出通道候选的梯度归约，以及分组原地累加的输出布局保护。
- [TorchNPU DTensor Dropout数据和mask分片](torch_npu_dtensor_dropout_mask_layout.md)：TorchNPU DTensor Dropout数据和mask分片的固定双版本本地规则、重分布边界与验收条件。
- [TorchNPU DTensor融合Attention布局、mask与本地派发](torch_npu_dtensor_fused_attention_layout_dispatch.md)：记录四个融合Attention分片策略、mask广播、统计和头数改写，保留反向kwargs维度差异。
- [TorchNPU DTensor分组Matmul列表策略与kwargs](torch_npu_dtensor_grouped_matmul_list_strategy.md)：TorchNPU DTensor分组Matmul列表策略与kwargs的固定双版本本地规则、重分布边界与验收条件。
- [TorchNPU DTensor损失归约与repeat分片边界](torch_npu_dtensor_loss_and_repeat_layouts.md)：区分CrossEntropy及KLDiv归约候选、均匀分片检查和repeat的维度及变量边界。
- [TorchNPU DTensor Matmul前反向候选与Partial梯度](torch_npu_dtensor_matmul_gradient_layouts.md)：TorchNPU DTensor Matmul前反向候选与Partial梯度的固定双版本本地规则、重分布边界与验收条件。
- [TorchNPU DTensor MoE隐藏维分片与概率梯度归约](torch_npu_dtensor_moe_hidden_sharding.md)：按固定双版本说明MoE置换与反置换候选布局、Partial概率梯度及主线v2差异。
- [TorchNPU DTensor归一化、RoPE和激活分片](torch_npu_dtensor_norm_rope_and_activation.md)：说明归一化复制范围、RoPE广播梯度Partial和SwiGLU及gather非操作维分片。
- [TorchNPU DTensor重分布、逐点策略与版本注册](torch_npu_dtensor_redistribution_and_registration.md)：说明位置与关键字参数重分布、非参与rank结果、逐点注册及旧版mesh展开补丁。
- [TorchNPU动态选择：输出定形、流同步与Where标量](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)：聚合Nonzero与MaskedSelect上界分配和同步定形、非连续out复制，以及Where真实标量谓词、dtype申请和设备搬运边界。并含 cpu_scalar 生成分支三例与主线独有边界。
- [Foreach执行：分批、Scalar准备与Host设备复制](torch_npu_foreach_batch_scalar_and_copy_routes.md)：聚合Copy/Add/Mul/Sqrt的fast与慢路线、V1标量物化和V2分块，并明确批量Host设备复制的dtype、连续性和同步边界。
- [TorchNPU发布版FSDP2：反向收尾与AllGather输入拷贝](torch_npu_fsdp_release_finalize_and_allgather_copy.md)：区分FSDP2基础NPU兼容补丁与增强缓存，说明反向等待、foreach输入准备和分区视图。
- [索引读取族执行：gather/index/index_select/index_fill 的派发与宿主读取](torch_npu_gather_index_fill_host_read_routes.md)：核对 gather 输出取 index 形状、反向 zeros+scatter_add 组合与主线与发布两版本 的 sparse_grad 差异，以及 index.Tensor 占位空张量、index_select 定形和 index_fill 在 950 的逐元素宿主读取路由。并含 count_nonzero 的 ne+sum 组合、_unsafe_index.Tensor 的 v2.1 原生委托与 select/index_fill dimname 负向定案。并含 _npu_index_add/_npu_index_add_ 的注册面、生成体与跨仓所有权。
- [对象gather的准备成本：尺寸同步、填充与HCCL路线](torch_npu_gather_object_padding_and_hccl_routing.md)：跟踪对象collective的padding、Host标量、allgather准备和版本目的rank差异。
- [ProcessGroupHCCL 剩余承重分支：ReduceOp 映射、集合通信前后钩子、字节对齐与心跳监控线程](torch_npu_hccl_collective_entry_residual_branches.md)：8194 行文件行为/分支映射后仍未入卡的承重面：getHcclReduceOp 的 AVG/PREMUL/bool 映射，allreduce 族仅取首张量与 bool 预转型、PREMUL 预乘、A5 整数 AVG 截断除，byte_alignment 的 950 免填充，getHcclCommConfig 的 CANN 8.2 确定性掩码，heartbeatMonitor 线程的 DumpPipe/全局 dump 信号协议。
- [TorchNPU HCCL 通信域创建阶梯：RankTable、子域派生、流选择与合并收集](torch_npu_hccl_comm_creation_ladder.md)：从 ProcessGroupHCCL 两版源码记录通信域创建回退链、P2P 域命名、RootInfo 广播与版本一致性告警、通信流 id 入口及 coalescing 组提交语义。
- [TorchNPU HCCL 通信域健康层：ASD 静默检查、看门狗错误轮询、NIC 主备切换、resume 与 NSLB 记录](torch_npu_hccl_comm_health_watchdog_and_nic.md)：从 ProcessGroupHCCL 两版源码记录 silenceCheck 触发门槛与缓存、Watchdog/checkHcclComms 异步错误处理模式、_set_switch_nic_comm 的 P2P rank 重编号、resume_hccl_comm 与 RESUME_MODE_ENABLE 的拷贝降级消费、NSLB 数据量与通信域记录及 waitForFutureOrTimeout 分支。
- [HiFloat8Tensor 包装类链：惰性导出、cast 内核与分派行为](torch_npu_hifloat8_tensor_wrapper_and_cast_chain.md)：解释 torch_npu.HiFloat8Tensor 两版本导出差异、_cd cast 内核与 __torch_dispatch__ 的 HIF8 保真范围。
- [索引写入与掩码填充：复制、动态定形和快捷路径](torch_npu_index_put_masked_fill_preparation_and_shortcuts.md)：聚合index_put与masked_fill的连续克隆、主线掩码快捷分支、布尔索引NonzeroV2同步、临时dtype转换和索引设备搬运边界。
- [索引写入族执行：index_copy/take/put_/masked_scatter/scatter 的派发与宿主成本](torch_npu_index_write_copy_scatter_host_routes.md)：核对 index_copy 的逐元素宿主循环与 clone、take 的 Gather 命令复用、put_ 的 ScatterNd 组合与拷回、masked_scatter 的 Bool 转换，以及 scatter 双路径的 dtype 处理与 reduce 字符串重载无回退的事实。
- [TorchNPU 旧 DataParallel 多卡通信：_C 绑定、通信域缓存与 scatter/gather 校验](torch_npu_legacy_dataparallel_comm.md)：记录 csrc/npu/DataParallelComm 的 HCCL 通信域缓存、按设备线程广播、容量上限、可用性回退与散聚校验，及两版仅排版差异的锚。
- [logsumexp/logaddexp/gcd：amax组合回退、ACE命令与注册CPU往返](torch_npu_logsumexp_logaddexp_gcd_routes.md)：区分logsumexp的aclnn直发与amax组合回退、logaddexp(2)的gen_opapi登记与LogAddExp命令、gcd.out的注册CPU往返，并核对Dimname版本边界与整数dtype提升。并含 logcumsumexp/logdet 零登记边界与 slogdet 双路实现。
- [成员判断与分桶：广播、排序和SearchSorted准备成本](torch_npu_membership_bucketize_and_searchsorted_routes.md)：核对isin数量启发式、unique与排序临时，Bucketize的950及类型门控，以及SearchSorted固定版本的校验、标量物化和输出格式准备。
- [Module迁移与权重格式准备：先后次序和参数副作用](torch_npu_module_device_transfer_and_weight_formats.md)：保存Module迁移前格式整理、JIT与类别门槛、Conv3d中间精度和版本device差异。
- [二元与杂项数学手写包装：标量过载分支、div 舍入模式及主线与发布两版本差异](torch_npu_native_binary_math_scalar_overload_routes.md)：汇总 g18 元素数学 45 个手写 opapi 登记名的包装行为：add/sub/mul 的 CPU 标量过载与 AddV3 运行时探测、div 六过载的 floor/trunc 模式映射与整型提升不对称、fmod 的 950 标量折叠、remainder 主线独有标量分支、log 的 dtype 协商、addcdiv/addcmul canCast 检查、atan2 主线与发布两版本 H2D 差异、complex 的 CPU 回退、nan_to_num 默认值表、pow/round.decimals/sgn 边界。并含npu_stride_add 内核合同与 ldexp_stub 覆盖。
- [比较、位运算、逻辑与移位算子：双派发路包装与Bool/标量不对称](torch_npu_native_comparison_bitwise_logical_shift_routes.md)：汇总eq/ne/gt/ge/le/lt、equal、bitwise与/或/异或、dunder移位、logical族、isneginf/isposinf、signbit的op_api与acl_op双路实现：CPU标量翻转、计算类型提升不对称、Bool输出与Long提升规则、950分支主线独有、生成spec与手写文件边界。
- [一元与逐元素数学生成包装路线：dtype 提升、整数恒等守卫与版本分支](torch_npu_native_elementwise_math_gen_routes.md)：汇总 g18 元素数学 121 个 gen_opapi 登记名的生成包装行为：struct_codegen 模板展开、逐族 dtype/size 公式（整型→Float、complex→实部、clamp 版本门控）、structured_inherit 委托、主线独有 integral_identity 守卫（round/trunc 整数恒等）与 round_/trunc_ 主线与发布两版本 派发差、angle 无 acl_op 回退边界。
- [TorchNPU原生分组GEMM的V5选择与布局成本](torch_npu_native_grouped_mm_layout_and_v5_selection.md)：说明原生_grouped_mm的四种布局、V5探测先后、编译期fallback、offset转换与有界测试。
- [普通范数执行：p路由、dtype与Foreach转换](torch_npu_norm_p_routes_dtype_and_foreach_preparation.md)：区分Norm与VectorNorm的p及CANN路由、输出dtype规则，并核对ForeachNorm的类型转换、标量输出与24项分批。并含 linalg_vector_norm 的 acl_op 回退内部：FP32中转、两段LpNorm命令与复数硬拒。并含普通 norm 的 acl_op 回退内部：无复数硬拒、FP32中转与硬 dtype 收口。并含 renorm/renorm.out/renorm_ 的 maxnorm 子张量重归一：FP16 中转、命名剥离版本差与独立原地符号。并含npu_renorm_backward 的 host 组合实现（主线独有）。
- [torch_npu 自有 pipelining：pipeline() 入口、FX 追踪与边界元数据 warmup](torch_npu_pipelining_fx_split_and_warmup.md)：记录主线 torch_npu.distributed.pipelining.pipeline 的 mode=fx 路径：原子单元叶子、SplitPoint 注入、warmup 元数据广播、Pipe 组装与 None 占位符修剪；发布版本 无此实现。
- [TorchNPU QAT的观察器状态与FakeQuant掩码](torch_npu_qat_observer_fake_quant_cachemask.md)：说明QAT双开关、可写观察器状态、移动平均、scale保护和Host FakeQuant掩码调用的版本边界。
- [普通归约与累加扫描：dtype、空输入和别名临时对象](torch_npu_reduction_scan_dtype_empty_and_alias_preparation.md)：聚合Sum/Mean/Prod/Cumsum的输出dtype选择、cumsum同对象out临时写回、sum空输入zeros快捷及命名维版本范围。
- [RepeatInterleave：输出长度、Host读数与反向准备](torch_npu_repeat_interleave_length_and_backward_preparation.md)：区分RepeatInterleave重载的output_size哨兵、Host标量读取、整数版本路由及反向view/sum或SDK准备。并含反向两名 custom 算子（repeat_interleave_backward_int/tensor）的 yaml 注册归属与 symint 段重复登记。
- [TorchNPU ShardedTensor.npu的拷贝、元数据与版本边界](torch_npu_sharded_tensor_npu_copy_contract.md)：区分ShardedTensor本地拷贝和全局元数据更新，保留device未消费与版本门控差异。
- [普通排序与TopK：符号路由、索引和旧ACL准备成本](torch_npu_sort_topk_routing_and_legacy_output_costs.md)：区分TopK V2能力路由、sort稳定性重载与argsort警告，并核对旧ACL非尾轴转置、INT32中间索引及out临时写回。并含 kthvalue/median/nanmedian 的 aclnn 路由、FP16 topk 组合回退与 nanmedian CPU 往返。
- [Unique动态输出：上界申请、同步与ViewShape回读](torch_npu_unique_dynamic_output_and_sync.md)：说明Unique2、UniqueDim和UniqueConsecutive的输出上界、inverse/counts准备、同步查询及版本守卫。
- [方差与标准差：correction分派和CPU往返边界](torch_npu_variance_std_correction_and_cpu_roundtrips.md)：明确Var/Std家族主线correction谓词触发的CPU计算与回写、发布版差异、正常路径兼容入口和输出维度准备。并含 nansum/nanmean 的无回退 aclnn 直发、整数 Long 提升与组合均值。

- [OpPlugin aclops 旧ACL公共内核层：十个回退算子的命令与准备行为](torch_npu_aclops_custom_common_kernels.md)：聚合utils/custom_functions/aclops中未被opapi卡片展开的十个旧ACL公共内核（zeros/embedding/where/sum/mean/var/index/gelu_backward/svd/repeat_interleave）的ACE命令、dtype/format准备与入口捷径，主线与发布两版本排版一致。
- [DDP Reducer 的 NPU 适配：物理元素数、梯度格式对齐与桶视图拷贝](torch_npu_ddp_reducer_npu_adaptations.md)：固定 reducer 在 NPU 上的差异点：NZ 语义的 physical_numel、grad 与参数格式不一致时的 npu_format_cast、copy_memory_ 桶拷贝与单设备事件计时，区分它与非 NPU 语义。
- [ProcessGroupLCCL：本地域集合通信后端的类型/算子约束与流同步](torch_npu_lccl_process_group_backend.md)：给出 LCCL 数据类型与 ReduceOp 映射（bool 求和改 MAX、AVG 等四算子不支持）、通信域缓存与专用流/事件同步链，明确其与 HCCL 后端的选择边界。
- [TorchNPU RPC TensorPipe 后端源级契约：注册、传输优先级与设备/流协议](torch_npu_rpc_tensorpipe_backend_source_contract.md)：固定主线源级核对 NPU_TENSORPIPE 后端注册与options校验、TP_SOCKET_IFNAME地址解析、传输/通道优先级、设备绑定、流与内存协议、超时生命周期及测试用Faulty注入边界。

- [FlexAttention反向任务列表：dK/dV开关与回退](flex_attention_backward_tasklist.md)：保留950PR/DT文档开关合同，并说明固定主线关键实现中没有该开关名的读取点，实际任务列表还依赖分派、资格与负载。
- [silent_check三代算子：v1 ACE、v2/v3 aclnn的梯度静默校验与fail-closed兼容](silent_check.md)：保存三版schema的原地更新标注语义、统计状态张量、参数下采样、v3视图元数据透传与DO_COMPATIBILITY双路失败行为，区分op层与ASD框架层；并给出 npu_asd_detect 的取值来源与 NPU_ASD_ENABLE 模式枚举（0..3 的两处独立解析与失败文案）。
- [TorchNPU 通信故障：输入连续性、建链等待与执行超时](torch_npu_collective_failure_triage.md)：按输入检查、Socket 建链和 Notify 执行阶段收敛故障，关注跨 rank 首个异常及缓冲区别名。
- [NPU_ASD_CONFIG：梯度特征值、冷却与 Checksum 联动](torch_npu_feature_value_detection.md)：说明长稳训练的异常检测、两层时间窗和三振计数，不把检测视为自动修复。
- [FlexAttention 反向分路：LSE 梯度、分离 dQ/dK/dV 与输出存储](torch_npu_flex_attention_backward_routes_and_gradients.md)：核对反向 mask-in/mask-out 的实际选择、log2 LSE梯度处理、FP32累加及广播还原，避免从前向成功推断全部梯度路线。
- [FlexAttention dK/dV 任务列表：选择、元数据缓存与拆分内存](torch_npu_flex_attention_dkdv_tasklist_runtime.md)：补齐显式 bwd_dkdv 分派的静态门槛、负载启发式、版本计数缓存及FP32 partial/reduce成本。
- [HCCL飞行记录器：输入身份、匹配分析和当前实现缺口](torch_npu_flight_recorder_analysis.md)：保留主线/发布版离线工具的参数差异、缺rank与版本校验，并说明静态发现的解析、报告和结果字段问题。
- [HCCL 状态采证：加载前配置、周期快照与失步分析](torch_npu_hccl_status_capture.md)：记录状态文件读取时机、默认间隔和 rank 身份，不把超时分析开关误作自动恢复。
- [TorchNPU Watchdog 与 HCCL 超时：检测和退出边界](torch_npu_hccl_watchdog_timeout.md)：说明异步错误处理、当前版本退出例外及 EI0002 的跨 rank 定位顺序。
- [计算通信重叠估时：NPU事件、合成分组与调度门槛](torch_npu_inductor_overlap_runtime_estimation.md)：解释overlap适配器的真实调用门槛、事件估时与GMM均衡group_list，区分缓存元数据、零占位值及端到端通信收益。
- [libtorch HCCL 单机示例：rank 映射与结果验收边界](torch_npu_libtorch_hccl_example.md)：对照主线和发布版示例识别设备编号、FileStore、构建路径与仅打印局部结果的边界。
- [Graph callable的静态绑定：预热、复制与输出别名](torch_npu_make_graphed_callables_static_binding_and_copies.md)：解释样例/参数静态绑定、warmup及replay复制与输出别名，不将autograd实现当产品支持。
- [MLIR/DVM共享分解：训练梯度、GELU选择与未注册辅助](torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)：区分MLIR/DVM共享分解的真实安装、空BatchNorm/卷积bias/softmax梯度、GELU精度和未注册RMS/SwiGLU/Rotary辅助；补后端lowering接线、快照恢复与设备分派机制。
- [原生Autograd Profiler：NPU设备与版本说明](torch_npu_native_autograd_profiler.md)：区分use_device与英文2.14迁移提示、原生报告工具和不支持的NVTX/ITT入口，不混用TorchNPU Profiler合同。
- [NPUGraph Tree 训练代际：待反向传播、输出克隆与梯度累加边界](torch_npu_npugraph_training_lifecycle.md)：对照固定主线和发布版实现，解释训练中何时允许结束 Tree 路径、存活输出如何跨代迁移，以及梯度缓冲为何需要独立处理。
- [Profiler内存类别推断：梯度、参数、激活与优化器状态](torch_npu_profiler_memory_category_inference.md)：解释tracer与dataflow分类顺序、id/key/version优先级及推断边界，避免把类别标签直接当作模型真实语义。
- [Triton矩阵分解与BatchNorm：梯度折叠、复制和舍入条件](torch_npu_triton_matmul_backward_and_batchnorm_decomposition.md)：区分普通与实验注册入口，记录padded ND折叠、按rank矩阵梯度路径、FP16保存统计量舍入及普通fast GELU。
- [GE批量更新转换：foreach标量、列表与整数别名](torchair_ge_foreach_lowering.md)：归并31组foreach实现的首元素类型选择、ScalarList差异、取整整数拆分及输出复用，限定准确重载与版本。
- [GE损失函数：归约索引、权重与梯度类型](torchair_ge_loss_lowering.md)：核对MSE与NLL前反向的类型提升、归约枚举、INT32目标和缺失权重分支，区分文档约束与静态构图边界。
- [Matmul训练分解：梯度布局、mask与类型替换](torchair_matmul_backward_decomposition_and_type_substitution.md)：说明matmul梯度的rank分支与contiguous成本、mask前置准备及类型替换参数缺口。
