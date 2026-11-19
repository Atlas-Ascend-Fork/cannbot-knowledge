# TorchNPU 训练接口

- [npu_fusion_attention：A2 训练入口、掩码与七返回](npu_fusion_attention.md)：限定发布文档的训练/Eager 范围，说明 mask 极性、TND 累计长度、dropout 与输出用途。

- [all_gather_into_tensor_uneven：单机非等长收集与同步返回](all_gather_into_tensor_uneven.md)：记录第零维分割、组大小和原地输出，区分文档返回标注与实际同步 None。
- [all_to_all_vc：全局计数矩阵与非原地变长通信](all_to_all_vc.md)：按组内 rank 解释发送行和接收列，检查元素数、连续布局及异步输出寿命。
- [get_hccl_comm_name：惰性初始化、副作用与全局 rank](get_hccl_comm_name.md)：区分后端注册、ProcessGroup 创建和 HCCL 实际初始化，记录 init_comm=False 的空字符串。
- [NpuFusedAdam：融合 Adam、L2 衰减与状态限制](npu_fused_adam.md)：记录构造参数、耦合衰减、AMSGrad 和稀疏梯度限制，关联融合存储契约。
- [NpuFusedAdamW：解耦衰减与参数对象稳定性](npu_fused_adamw.md)：记录默认权重衰减及构造器范围，避免从源码注释推定 maximize 等额外参数可用。
- [NpuFusedLamb：Trust Ratio、默认 epsilon 与待核验分支](npu_fused_lamb.md)：限定默认全局范数关闭的路径，记录注释默认值及辅助方法缺口，避免未验证的收敛保证。
- [NpuFusedSGD：必填学习率与 Nesterov 条件](npu_fused_sgd.md)：以真实构造器限定动量和 Nesterov，记录文档对零动量条件的遗漏。
- [reduce_scatter_tensor_uneven：单机分割归约与输出缓冲区](reduce_scatter_tensor_uneven.md)：限定输入第零维分割及单机范围，记录 PRODUCT 限制、异步句柄与同步返回差异。
- [reinit_process_group：重建分支、恢复范围与返回差异](reinit_process_group.md)：区分接口文档与固定 Python 实现，避免把通信域处理当成完整训练状态恢复。

- [npu_apply_adam_w：950 Eager 的 out 原地更新](npu_apply_adam_w.md)：说明必须提供 var/m/v、无 out 实现拒绝，以及 AMSGrad 描述不等于当前支持 True。
- [npu_cross_entropy_loss：训练参数限制与四个返回槽](npu_cross_entropy_loss.md)：说明仅 loss 支持梯度、requires_grad 下的归约限制以及暂未支持的 zloss 选项。
- [npu_fused_cross_entropy_loss_with_max_sum：消费全局统计](npu_fused_cross_entropy_loss_with_max_sum.md)：说明 A2/A3 的全局统计前提、label_smoothing=0 与可选 FP32 softmax 输出。
- [npu_fused_linear_cross_entropy_loss_with_max_sum_backward：两种反向路线](npu_fused_linear_cross_entropy_loss_with_max_sum_backward.md)：说明 packed mask、词表分片大小及 softmax 缓存与重计算的互斥输入关系。
- [npu_fused_linear_online_max_sum：词表分片的局部统计](npu_fused_linear_online_max_sum.md)：说明 MatMul 与损失前处理的六输出、bit mask 和性能/显存分支，不把局部量直接当全局结果。
- [npu_group_norm_swish：缩放、反向分组与确定性](npu_group_norm_swish.md)：说明同 dtype 仿射、每组通道数不超过4000的训练约束及 A2/A3/950 的反向确定性差异。

- [npu_add_quant_gmm_：分组量化梯度和尺度容量](npu_add_quant_gmm_.md)：说明K轴累计边界/计数、未更新区域、组间MX尺度pad和group_sizes只能None。
- [npu_add_quant_matmul_：950量化梯度原地累加](npu_add_quant_matmul_.md)：说明FP8 MX与HiF8两类尺度、group_sizes固定组合和CANN 9.0入口检查。
- [npu_grouped_matmul_add_：微批梯度的原地FP32累加](npu_grouped_matmul_add_.md)：说明950训练单算子的输入alias与K轴分组，不继承无下划线页的图及产品范围。

- [npu_dense_lightning_indexer_grad_kl_loss：稠密warmup与三路梯度](npu_dense_lightning_indexer_grad_kl_loss.md)：说明teacher与Indexer两套统计、仅返回Indexer梯度及FP32单元素loss，限制主头数和D。
- [npu_dense_lightning_indexer_softmax_lse：稠密评分的max/sum预计算](npu_dense_lightning_indexer_softmax_lse.md)：说明训练Indexer稠密KL的前置统计、FP32输出和累计长度列表，区分max值与索引。
- [npu_sparse_lightning_indexer_grad_kl_loss：稀疏KL与sinks入口](npu_sparse_lightning_indexer_grad_kl_loss.md)：说明teacher D=512、稀疏索引和独立Indexer梯度，明确不支持图及950额外头数组合。

- [npu_fused_floyd_attention：五维双路径注意力与反向统计](npu_fused_floyd_attention.md)：说明 Floyd 注意力的五个输入、max/sum/out 返回顺序、形状倍数和反向非确定性。
- [npu_scaled_masked_softmax：缩放、广播掩码与形状限制](npu_scaled_masked_softmax.md)：记录预留上三角开关只支持 False、H/W 对齐范围和 950 与旧产品的执行路径。

- [PyTorch SDPA：NPU 掩码语义与融合路径选择](scaled_dot_product_attention.md)：说明原生 SDPA 的四维规格、布尔与加性掩码、MATH 控制、版本重载及 950DT 入图限制。并含 _transform_bias_rescale_qkv 探测失败整对 CPU 往返。

- [确定性前后向标记：Tensor 依赖与反向切换](deterministic_with_backward.md)：合并说明 enable/disable_deterministic_with_backward 的全局布尔副作用、梯度依赖和禁图条件。
- [set_deterministic_level：全局等级、布尔状态与 CANN 门槛](set_deterministic_level.md)：说明 0..3 等级、动态修改、失败恢复和 Runtime/算子包双重条件，避免只检查 Python 标志。

- [确定性未初始化内存填充：NPU显式启用](fill_uninitialized_memory.md)：记录fill_uninitialized_memory属性默认值与NPU实际填充条件，区分算子确定性、随机状态和HF32。

- [HCCL Python入口：ProcessGroup构造与后端可用性](hccl_process_group_and_availability.md)：区分直接构造ProcessGroupHCCL、后端可用探测和通信已初始化，保留超时参数文档边界。
- [NpuFusedAdadelta：默认参数、rho边界与融合状态](npu_fused_adadelta.md)：保存Adadelta构造与非负约束，区分接口默认值和一次step样例的验证范围。
- [NpuFusedAdamP：投影阈值、衰减比例与动量选项](npu_fused_adamp.md)：保存delta、wd_ratio、Nesterov参数，限定局部投影实现与未验证的算法组合。
- [NpuFusedBertAdam：学习率身份、warmup与梯度范数](npu_fused_bert_adam.md)：保留文档lr默认值与发布构造required差异，限定schedule、beta及裁剪参数。
- [NpuFusedOptimizerBase：构造、继承与首次参数组合](npu_fused_optimizer_base.md)：明确基类需子类实现更新，保存default字典、FP16/FP32与一次组合的前提。
- [NpuFusedRMSprop：平滑、centered与非负参数](npu_fused_rmsprop.md)：保存RMSprop构造、平滑与动量约束，区分普通和TF变体状态。
- [NpuFusedRMSpropTF：初值、epsilon和动量差异](npu_fused_rmsprop_tf.md)：区分TF变体默认值与注释冲突，保留衰减/动量开关及状态初值。

- [NPU Autocast状态API：可选dtype、当前dtype与使能状态](autocast_state.md)：区分支持列表和当前配置，保存默认FP16与五个独立查询/设置入口。
- [HF32与CubeMathType属性：卷积、矩阵乘和950DT回退](hf32_and_cube_math_type.md)：区分三个布尔属性默认值与五种枚举，保留未配置None及USE_FP32_ADD的算子例外。
- [NPU溢出查询API：Inf/NaN输入检查与硬件状态](overflow_state.md)：保存两模式不同语义、隐式Host同步与清除行为，保留950文档冲突和FORCE版本门槛。

- [add-softmax-dropout组合：融合门控与回退状态差异](contrib_add_softmax_dropout.md)：保存4D、尺寸和32整除门控，指出dim未消费及示例实际走回退路径。
- [BERT融合注意力旧包装：NZ约束、首次检查与LayerNorm返回](contrib_bert_fused_attention.md)：区分两个Function的参数、输出和梯度，保留一次校验缺口及keep_prob默认身份。
- [contrib BiLSTM：双单向拼接与旧接口迁移](contrib_bidirectional_lstm.md)：保留废弃计划、序列维翻转和实际Tensor返回，不把旧docstring视为完整原生LSTM合同。
- [byte-mask Dropout：弃用状态、概率与禁止原地](contrib_byte_mask_dropout.md)：合并函数和模块的公共合同，保留inplace文档与包装拒绝差异及max_seed预留身份。
- [缓存Dropout：Fairseq别名、预热与共享掩码队列](contrib_cached_dropout.md)：保存无动态shape、掩码缺失时透传及eval边界，区分Cached与PreGen的状态协议。
- [ChannelShuffle：双输入、分片输出与反向缺口](contrib_channel_shuffle.md)：限定groups=2，区分split返回类型、索引重写和非split训练的梯度槽问题。
- [contrib Mish、SiLU与Swish：别名和原生迁移](contrib_deprecated_activations.md)：记录三个旧激活入口及替代名称，保留历史说明而不承诺新模型性能收益。
- [NpuDropPath：样本路径随机深度与预生成队列](contrib_drop_path.md)：保存默认None缺口、首次透传和训练状态，区分随机深度与逐元素Dropout。
- [Focus模块：空间切片、通道拼接与Conv链路](contrib_focus.md)：保存构造参数和实际LeakyReLU/BN路线，不把fuseforward当已完成权重融合。
- [FusedColorJitter旧接口：Host实现与参数错位边界](contrib_fused_color_jitter.md)：保留ColorJitter迁移、随机区间和Host路径，指出当前固定包装不能作为可靠设备增强配方。
- [LabelSmoothingCrossEntropy：类别数、标签与FP32归约](contrib_label_smoothing.md)：保存平滑范围及真实one-hot维度，区分类别默认值和预测列数必须一致的前提。
- [matmul_transpose：末两维转置与定制反向](contrib_matmul_transpose.md)：区分Q乘KT和普通matmul，纠正文档动态限制误植并保留broadcast边界。
- [ModulatedDeformConv：pack输入、FP32与索引寿命](contrib_modulated_deform_conv.md)：说明DCNv2别名、默认bias更正和偏移初始化，保留迁卡及反向保存条件缺口。
- [contrib MultiheadAttention：融合开关、特殊forward与未消费参数](contrib_multihead_attention.md)：保存默认返回空元组、私有融合配置及缓存Dropout依赖，避免按原生MHA直接替换。
- [contrib Prefetcher：二元批次、复用流与耗尽协议](contrib_prefetcher.md)：区分非阻塞搬运和实际重叠，保存构造预取、next等待及重复初始化条件。
- [Swin Roll包装：H/W索引缓存与设备边界](contrib_swin_roll.md)：记录4D、两项shifts/dims、实际滚动轴及缓存漏设备条件。

- [旧激活函数：fast_gelu、Mish与SiLU的迁移边界](legacy_activations.md)：区分近似GELU与旧Mish/SiLU计划废弃入口，保留名称和dtype差异。
- [旧Adam更新：out状态、BERT参数与废弃迁移](legacy_adam_updates.md)：保留低层状态写回协议、Scalar声明与非out入口报错，避免机械替换优化器。
- [旧卷积包装：参数顺序、权重布局与functional迁移](legacy_convolutions.md)：覆盖2D/3D卷积及转置卷积，强调低层声明无默认值和转置参数重排；含未融合/slow conv 13 名注册面；含 slow conv 两支专用 aclops backward 内部：三命令分解、output_mask 门控不对称与 BiasAddGrad 输入字面。并含npu_conv_transpose2d/convolution_transpose 与 3D 反向的 aclops 实现层。
- [_npu_dropout：不透明掩码、默认生成器与版本路径](legacy_dropout.md)：解释无seed形参不等于没有RNG状态，区分私有训练操作和原生Dropout端点。
- [旧浮点状态Tensor：alloc/get/clear及不维护边界](legacy_float_status.md)：区分状态Tensor和新溢出API，保留get返回类型与clear结果不保证零值的实际路径。
- [旧GRU/LSTM：低层中间输出与单层约束](legacy_gru_and_lstm.md)：区分低层六/八输出和nn模块协议，不复制文档中的缺省参数及方向拼写。
- [旧线性与BMMV2：矩阵形状、格式和输出尺寸](legacy_linear_and_bmm.md)：记录二维Linear约束、BMMV2的INT8拒绝及替换时的广播/形状边界。并含npu_bmmV2 aclops 实现层（pure_bmm_v2/reshape helper/反向接线）。
- [旧极值与排序：INT32索引、返回元组及轴差异](legacy_min_max_and_sort.md)：区分npu_max/min的双输出和sort_v2仅值输出，保留命名维版本限制。并含 torch.max/min pairwise out= 的发布独有注册边界。并含 amax/amin 的 gen_opapi 登记与 acl_op ReduceMax/ReduceMin 回退。并含 torch.max/min dim 族的 Long 索引、ArgMax/ArgMinWithValue 回退与 Dimname 编译边界。并含 argmax.out/argmin/argmin.out 三名：无 dim 展平、keepdim 不对称与 ArgMaxV2/ArgMin 命令差异。并含 max 系 sparse 标记消费路径：SparsePrivateUse1 生成链与 to_dense 后重分发。
- [npu_one_hot：num_classes实际是插入轴](legacy_one_hot.md)：区分旧自定义接口的axis/depth和普通one_hot类数，保留旧路径自动推深度限制。
- [npu_random_choice_with_mask：有效项、坐标与count限制](legacy_random_choice_mask.md)：保留bool输入、随机种子和固定长度输出，纠正文档count零值与实际检查冲突。
- [旧Softmax交叉熵：稠密标签、逐行loss与无默认均值](legacy_softmax_cross_entropy.md)：区分同shape浮点标签和类别索引，纠正展平示例对batch语义的误导。

- [旧加法Softmax-Dropout：概率、掩码和反向限制](legacy_dropout_add_softmax.md)：纠正1/prob公式和四维mask描述，保留融合形状门槛与不维护状态。
- [旧fused_attention_score：NZ、保留概率与固定自注意力shape](legacy_fused_attention_score.md)：保留旧产品平台未知及真实二维输出，不用文档宽松描述推导任意交叉注意力。
- [旧MultiHeadAttention融合接口：八输出和压缩掩码](legacy_multi_head_attention.md)：区分nn模块与19参数低层入口，纠正keep概率及输出dtype描述。
- [npu_deformable_conv2d：采样中间量、dtype和产品路径](npu_deformable_conv2d.md)：保留四元素步长/膨胀、offset通道数及950单算子模式，不当普通conv等价替换。

- [npu_sim_exponential_：原地指数分布与跨版本RNG偏移](npu_sim_exponential.md)：保留连续ND输入、lambda边界和主线计数算法，不承诺跨版本随机序列相同。

- [batch_norm_reduce：通道和、平方和与保留eps](batch_norm_reduce.md)：明确BatchNorm归约的双FP32输出、NCHW通道轴及未参与计算的必填eps，限定A2/A3。

- [npu_fusion_attention_v2：训练RoPE、PSE顺序与随机数版本边界](npu_fusion_attention_v2.md)：按固定主线限定A2/A3/950训练V2入口，说明RoPE与PSE组合、七输出和梯度、发布实现差异及Meta限制。

- [npu_fusion_attention_v3：训练图模式、张量随机数与更新边界](npu_fusion_attention_v3.md)：限定A2训练V3六Tensor返回，区分公开BNSD图合同、CPU变长前缀及主线TND workspace/out更新路径。

- [Bert旧训练入口组：QKV-LN前向、相对位置掩码softmax、注意力softmax与DeepNorm](legacy_bert_qkv_softmax_and_deep_norm.md)：记录四个无文档页的Bert/Megatron时代训练注册入口的host检查、输出合同、反向链路、Meta差异与主线与发布两版本版本边界（含qkv前导检查的&&与||语义差异）。并含npu_fused_attention_qkv_grad 双 ACE 命令反向。
- [npu_quant_fusion_attention：量化QKV训练打分与前反向的950入口](npu_quant_fusion_attention.md)：保存固定无dropout/全窗语义、dequant scale门槛、950前向query_dtype必传的发布/主线差异、BF16输出分配、pre-950分派边界与Meta静态缺陷。
- [npu_ring_attention_update：分步Attention与Softmax统计合并](npu_ring_attention_update.md)：说明SBH/TND输入、FP32八槽统计、长度校验、V2调用与仓内参考测试的适用边界。

- [contrib FastBatchNorm：num_batches_tracked 的 int32 化与同步回退边界](fast_batchnorm_int32_count.md)：保存 contrib FastBatchNorm1d/2d/3d/FastSyncBatchNorm 的计数缓冲 int32 化语义、momentum=None 的宿主回读、同步门控与框架 BN 回退及转换辅助的适用范围。

- [TorchNPU C++ HCCL：ProcessGroup与批量P2P合同](cpp_processgroup_hccl.md)：保存Backend构造、通信成员与Work完成点，区分batch_isend_irecv的版本签名和global rank。
- [FlopsCounter：重计算计数、状态切换与返回顺序](flops_counter.md)：保存单例计数状态图和pause语义，区分FLOPs计数、MFU/HFU与运行测量。
- [save_async：后台线程、模型Hook与保存完成边界](save_async.md)：保存序列化参数、无返回完成句柄及每设备流复用限制，不把异步返回当检查点落盘。
