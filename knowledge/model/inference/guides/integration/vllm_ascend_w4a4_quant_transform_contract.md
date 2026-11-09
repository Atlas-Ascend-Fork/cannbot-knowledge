---
type: Guide
title: vLLM Ascend W4A4适配：格式选型、变换矩阵与FP4活动存储
description: 聚合整数FlatQuant、LAOS、MXFP4及MXFP4-FlatQuant的权重与激活合同，核对Kronecker分解、32768分块、clip_ratio主机缓存、TP矩阵与MX组相位、packed参数改名、ND转置及MoE输入释放和EPLB活动视图；按实际scheme保留设备、重载与性能边界。
aliases:
- AscendW4A4FlatQuantDynamicLinearMethod
- AscendW4A4LaosDynamicLinearMethod
- AscendW4A4MXFP4FlatQuantDynamicLinearMethod
- AscendW4A4MXFP4DynamicLinearMethod
- AscendW4A4MXFP4DynamicFusedMoEMethod
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a4/w4a4_flatquant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a4/w4a4_laos_dynamic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a4/w4a4_mxfp4_flatquant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a4/w4a4_mxfp4.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a4/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a4/test_w4a4_flatquant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a4/test_w4a4_laos_dynamic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a4/test_w4a4_mxfp4_flatquant_dynamic.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/quantization/methods/w4a4/test_w4a4_mxfp4.py
  role: evidence
created_at: '2026-11-02T12:37:48Z'
updated_at: '2026-11-02T12:37:48Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend W4A4适配：格式选型、变换矩阵与FP4活动存储

## 先选择真实scheme

新模型采用W4A4时，先区分整数INT4、微缩放FP4以及是否带FlatQuant变换。四种实现的checkpoint参数、scale、量化算子和后处理不同；修改配置字符串不会完成格式转换。本卡聚合Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2下的具体合同，服务加载适配、静默精度排查与峰值内存归因。

已全文读取四个scheme：w4a4_flatquant.py210行、w4a4_laos_dynamic.py91行、w4a4_mxfp4.py477行、w4a4_mxfp4_flatquant.py198行，family导入30行，以及四个直接关联UT220/60/428/201行，共9个来源1915行。源码和测试仅作数据，未导入上游、运行UT、加载模型、执行TorchNPU/CANN、通信、图、精度或性能实验。整项硬件与模型范围未知，保持draft、空平台和framework=vllm部分Scope。

以下N表示Linear输出宽，H表示输入宽，E表示专家槽数，I表示本rank intermediate宽，G表示量化group大小。shape是Host Tensor约定，不代替真实设备格式和算子ABI验收。

| 注册键与具体类 | 参数和激活路线 | 首要接入检查 |
| --- | --- | --- |
| W4A4_FLATQUANT_DYNAMIC / AscendW4A4FlatQuantDynamicLinearMethod | INT8容器保存未打包INT4，加载后生成INT32 weight_packed；Kronecker变换并量化激活 | H整除8、左右变换矩阵、clip host值与分块 |
| W4A4_DYNAMIC / AscendW4A4LaosDynamicLinearMethod | INT4 pack权重；激活动态量化为quint4x2 | FP16 matmul中间输出与bias位置 |
| W4A4_MXFP4 / AscendW4A4MXFP4DynamicLinearMethod、AscendW4A4MXFP4DynamicFusedMoEMethod | UINT8容器保存打包FP4，激活也为FP4，scale语义为E8M0 | packed名字、TP组相位、ND stride与活动专家存储 |
| W4A4_MXFP4_FLATQUANT / AscendW4A4MXFP4FlatQuantDynamicLinearMethod | FP4权重和激活叠加Kronecker变换 | 配置的TP上限、RowParallel左矩阵对角块 |

注册条目不等于当前进程已导入实现或算子已运行。通用[scheme接入](vllm_ascend_modelslim_scheme_adaptation.md)及[compressed-tensors分派](vllm_ascend_compressed_tensors_dispatch.md)继续负责配置识别；本卡不重新定义全模型量化策略。

## 整数FlatQuant与LAOS

整数FlatQuant先创建INT8 `[N,H]` weight及FP32 per-channel weight_scale/weight_offset。get_weight要求H整除8，并把input_size写到类属性；随后get_pertensor_param据该值分配左右方阵和单元素clip_ratio。调用顺序必须保持同一层的尺寸对应，不能在交错构造不同层时把类级尺寸当作实例私有状态。实现没有在这几步统一检查全部正值或形状。

solve_kronecker_decompose以差平方求两个因子；apply要求left_dim×right_dim等于实际输入宽。普通输入先view成三维再调用Kronecker量化；prepare_input_for_overlap只接受二维输入，返回已经量化的PreparedLinearInput。Prepared路径要求scale非None并保留output_dtype，避免重复变换；不因包装类型存在就推定scale与输入身份已经验证。

batched_kronecker_quant仅在该整数FlatQuant路线把dim0超过32768的输入切块，分别调用npu_kronecker_quant，再沿dim0拼接量化结果和scale。恰好32768走单次调用。此阈值来自固定Host workaround，不是所有W4A4方案、模型batch或硬件的统一上限；MXFP4-FlatQuant直接调用该量化算子，没有复用这个分块wrapper。

整数FlatQuant后处理用npu_convert_weight_to_int4pack生成weight_packed，注册后删除原weight；左变换矩阵转置并contiguous，scale/offset和clip_ratio转换FP32，aclnn_clip_ratio通过item保存为主机标量。forward使用weight_packed.t()和展平scale，matmul中bias=None，最后才加模型bias并恢复原输入前导shape。weight_offset虽然分配和转换，当前forward没有显式把它传给matmul；不能仅凭参数存在推导非零非对称offset已被正确消费。

LAOS不执行Kronecker变换，原始weight同样为INT8 `[N,H]`；后处理转INT32并pack，再transpose最后两轴。输入动态量化目标为quint4x2，matmul显式输出FP16，随后转回输入或Prepared记录的dtype，再加模型bias。与“matmul直接输出BF16”不同，末尾cast不能恢复FP16中间路径已经丢失的信息；真实误差仍需数值比较。本实现也创建weight_offset，但当前apply不显式传入它。

更新clip_ratio Tensor不会自动改写已经缓存的Python标量；若发生重载，需要确认真实caller刷新aclnn_clip_ratio。相关[RFork加载指南](vllm_ascend_rfork_processed_weight_loading.md)另有预布局和host状态刷新合同，不能为更新一个标量而盲目重复整个pack/transpose。上述后处理没有提供本族统一的幂等标记、回滚或在线更新事务。

## MXFP4-FlatQuant的矩阵与TP门禁

该scheme读取group_size（缺省32）、max_supported_tp（缺省4）及真实TP大小，超过配置上限会ValueError；它不证明上限内所有TP、尺寸和模型组合都已通过。get_weight只显式拒绝奇数H，创建UINT8 `[N,H//2]`，scale为UINT8 `[N,H//G]`；整数除法不替代完整group整除检查。

get_decompose_dim先求分解因子并检查较大因子是否超过256，必要时采用一个维度256的回退。回退计算仍需核对实际返回shape，不能把常量256当成所有返回维度均受同一完整校验的证明。

非RowParallel按本地H创建左右矩阵。RowParallel则根据本地H×实际TP、配置max_supported_tp计算较大的左矩阵，后处理按layer.tp_rank/tp_size取左矩阵的对角块；随后转置左矩阵、处理scale和权重。矩阵checkpoint、加载分片、配置TP与层对象TP必须一致，不能只因切片未报错就认为跨rank变换已经数学等价。

FP4-FlatQuant将scale成对reshape再transpose，权重只transpose，没有整数INT4重新pack步骤。其Kronecker输出和matmul均显式声明FP4语义，scale/per-token scale为E8M0，bias直接交给matmul，output_dtype跟随原输入或Prepared。这与整数FlatQuant在matmul后相加bias的路线不同；不要仅复用参数名而遗漏运算位置及精度差异。

## 普通MXFP4：checkpoint名字、TP组相位与ND

普通W4A4_MXFP4按quant_config.get_name是否为compressed-tensors选择weight_packed或weight；MoE同样为w13/w2选择_packed后缀。后处理先由_rename_packed_weight_parameter将packed属性的数据接到标准名字的新Parameter，再删除旧属性。它不是通用权重转换器，也不保证外部持有的旧Parameter引用自动更新。

Linear权重为UINT8 `[N,H//2]`，scale用cdiv(H,G)创建。它显式声明supports_unaligned_tp_groups=True和supports_weight_switch=True，weight与scale的输入/输出gather轴分别为0/1；这些opt-in不能自动赋给另外三种scheme。[scale分片排障](../../runbooks/precision/vllm_ascend_quant_scale_tp_sharding.md)和[权重切换](vllm_ascend_weight_switch_contract.md)继续维护通用loader与缓冲所有权。

RowParallel后处理根据tp_rank×input_size_per_partition计算全局MX组相位，前缀恢复原group边界，后缀补齐最后group。激活按逻辑K补零，打包权重的byte padding是对应逻辑数量的一半；若前/后padding不是偶数会拒绝。apply通过mxfp4_tp_padding在相同位置补激活，再以round_mode=round进行动态FP4量化。

scale最后维若为奇数，会补一个0字节再成对reshape；不能把E8M0容器中的字节0直接解释为普通浮点零。Linear的weight及scale转置后保持ND，即使全局weight_nz_mode开启也不调用NZ转换。不要为“统一布局”强制contiguous/NZ，破坏固定算子依赖的stride。普通输入支持先展平多维激活再恢复前导shape，二维overlap路径则使用Prepared；传入bias会先转FP32再交matmul。

这些具体补齐与ND规则属于本scheme，不能移植成[W4A8_MXFP重载卡](vllm_ascend_mxfp4_weight_reload_contract.md)的默认行为；后者使用FP8激活、不同NZ处理和恢复marker。

## MoE活动存储与输入寿命

普通MXFP4 MoE创建UINT8 w13 `[E,2I,H//2]`、w2 `[E,H,I//2]`及各自group scale，后处理先处理packed名字，再分别补齐奇数scale group。非Mega路线只transpose权重和scale，保留FP4分组算子使用的转置stride。

get_eplb_weight_views显式返回两组weight和两组scale的transpose视图，supports_eplb=True；专用UT在非Mega mock路线定义这些视图与活动Tensor共享storage并保持专家轴。能力flag和共享指针不等于真实迁移事务已经完成，仍按[EPLB接入指南](vllm_ascend_eplb_model_weight_contract.md)验证映射、连续重排与提交。

Mega路线在转置前建立每专家weight clone/NZ列表，把scale clone后view为实际E8M0 dtype，再dispose原四个聚合参数。runtime getter根据use_mega_moe选专用列表或聚合Tensor，但EPLB view getter仍直接访问聚合字段；不能从supports_eplb=True外推Mega与EPLB组合已经闭合。两条fused payload均将scale_bias设为None，也不因getter存在就声明所有通信消费者接受该组合。

MoE只将silu列为融合激活。gmm1_act_quant和普通gmm1都区分输入所有权：没有dispatcher提供的dynamic_scale时，先量化成独立FP4激活，再dispose原输入，随后launch GMM1；已有scale时，GMM1直接消费原激活，调用后才dispose。前者减少原输入与GMM分配的重叠是代码动机，本卡没有实测峰值或加速数字。更改顺序前需核对量化结果是否独立、是否还有别名或在飞读者，Python调用返回不是全部设备消费完成的证明。

GMM调用显式传FP4的x/weight语义及E8M0 scale，不能把UINT8 storage直接解释为整数UINT8计算。gmm2对原BF16/FP16保持相应输出dtype，对UINT8/FP4等按代码选择BF16，否则选择FP16；输入存储dtype、逻辑激活dtype和模型输出精度分别核对。[Gemma4视觉塔](vllm_ascend_gemma4_tower_quantization_contract.md)已有按逻辑model_dtype准备像素输入的独立合同。

## 新模型验收顺序与停止条件

先记录实际registry键、scheme/wrapper、checkpoint命名、逻辑H/N/E/I/G、原始和活动weight/scale的shape/dtype/stride、矩阵维度、TP rank/world、padding及clip主机值。优先验证一层的非零参考计算、bias位置和dtype，再验证完整加载、预量化输入、分块边界、TP相位及MoE存储路线；不要用模型能启动代替精度。

四套UT仅定义CPU/mock下的shape、getter、矩阵门禁、分块调用、字节视图、ND/stride和dispose先后关系，没有在本次执行，也不能证明真实NZ、CANN数值、所有激活/通信组合、图、EPLB迁移或重载安全。遇到参数名、group相位、矩阵或活动owner不匹配时，先停止新增优化并恢复匹配的checkpoint与配置，不能靠丢scale/offset或强制布局掩盖。

正确性与生命周期闭合后，再固定硬件、版本、模型、token形状与拓扑比较转换/clone峰值、Kronecker和量化开销、GMM及通信、端到端TTFT/TPOT。低位宽、局部释放或存在融合入口都不构成泛化收益承诺。本卡没有真机、模型精度或Agent效果结果。
