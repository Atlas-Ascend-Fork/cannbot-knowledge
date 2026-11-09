---
type: Guide
title: vLLM Ascend静态图桥接：ONNX属性转换、Attention子图与tiling sink
description: 对照固定Main的ONNX parser与GE子图，核对opset/domain、输入输出序号、scale/dropout默认值和mask构造；分析tiling sink缺源返回、设备注册与workspace任务ABI，以及transpose tiling/key的shape和位宽约束，区分图转换成功与设备执行证明。
aliases:
- ParseParamsNpuFusedAttentionScoreFwd
- ParseOpToGraphNpuFusedAttentionScore
- ParseOpToGraphNpuMaskedSoftmaxWithRelPosBias
- ParseParamsMultiHeadAttention
- tilingsink::TilingAicpuTask
- GetDataCopyTransposeTiling
- optiling::DeviceOpImplRegistry
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/framework/onnx_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/graph/error_codes.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/op_graph/op_transformer_proto_extend.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/data_copy_transpose_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/data_copy_transpose_tiling_def.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_base/tiling_type.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_sink/device_op_impl_registry_impl.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/tiling_sink/tiling_aicpu_task.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/embedding_bag_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/fillwindowcache_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/multi_head_attention_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/npu_fused_attention_score_fwd_onnx_plugin.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/npu_fused_attention_score_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/npu_masked_softmax_with_relposbias_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/npu_scaled_masked_softmax_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/framework/tfidf_vectorizer_onnx_plugin.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/tiling_base/tiling_util.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/tiling_sink/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/tiling_sink/tiling_sink_registry.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/inc/framework/stub_ops.h
  role: constraint
created_at: '2026-11-03T05:38:00Z'
updated_at: '2026-11-03T05:38:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---
# vLLM Ascend静态图桥接：ONNX属性转换、Attention子图与tiling sink

## 使用范围

本文固定Main `ceac1a2`的公共ONNX→GE parser、子图构造和tiling sink支撑代码。它不同于[Torch图融合pass](vllm_ascend_graph_fusion_pass_contract.md)，不证明当前vLLM模型默认经过ONNX/GE，也不把parser注册等同于CANN内核已编译或可执行。框架桥接与stub基础见[GE到ACLNN公共桥接](vllm_ascend_ge_aclnn_fallback_contract.md)。

framework CMake只在BUILD_OPEN_PROJECT且非BUILD_OPS_RTY_KERNEL时加入ONNX plugin源。OriginOpType同时含domain/opset和名称，导出同名节点却使用不同domain/version不保证命中。ImplyType::TVM是此注册的实现类型标记，不是目标设备算法已验证的证据。

## ONNX属性转换矩阵

| parser | 注册的来源节点 | 固定转换与默认值 |
|---|---|---|
| EmbeddingBag | ai.onnx opset8–16 | mode只在STRING属性存在时写入；scale_grad_by_freq、sparse、include_last_offset默认为false，整数非0为true |
| FillWindowCache | ai.onnx opset8–18 | axis/cache_depth默认为0；reinterpret NodeProto只判空，不提供dynamic_cast的类型检查 |
| NPUMultiHeadAttention | ai.onnx opset11–18、npu::1 | head数、每head维、src/tgt长度、dropout_prob、softmax_use_float六项按类型计数；恰好6项才通过；keep_prob=1-dropout_prob |
| NPUScaledMaskedSoftmax | ai.onnx opset11–18、npu::1 | scale默认1；fixed_triu_mask默认false且只有INT值1才开启 |
| NPUMaskedSoftmaxWithRelPosBias | ai.onnx opset11–19、npu::1 | parser默认scale_value=0、inner_precision_mode=1；与所读GE OpDef的1/0默认相反，缺属性仍可能静默覆盖模型意图 |
| NPUFusedAttentionScore/Fwd | ai.onnx opset11–18、npu::1 | 必须恰有一个FLOAT scale；keep_prob默认1，四个transpose默认false，INT恰为1才true；构造成PartitionedCall子图 |
| TfIdfVectorizer | ai.onnx opset9–18 | 按名称及INT/STRING/FLOATS/INTS/STRINGS类型转移gram/skip/mode/weights/counts/indexes/pool；未做全部业务完整性检查 |

上述“属性计数”不是去重后的字段集合校验，重复属性也会影响计数；SetAttr返回值多数没有逐个核验。MultiHeadAttention没有在parser证明head/维度为正、dropout概率有效或shape一致。GetOpName失败仅返回字符串None，不会自行使所有parser失败。Agent应保留原始属性存在性、类型和值，不能只比较转换后节点名称。

## Attention子图的新增节点与形状假设

两个FusedAttention parser先按ONNX输入/输出数注册动态口，但ParseOpToGraph实际固定创建data0..3，分别接query/key/value/padding_mask。它读取第0输入shape并直接令dims[3]=dims[2]，构造`[B,N,S,S]` dropout mask，再把scale常量Cast为FP16、接AttentionScore、softmax_axes固定[-1]。动态口注册不证明任意输入数、rank或非方形Q/K长度被处理。

普通NPUFusedAttentionScore再把Fill生成的mask Cast到FP16，只暴露AttentionScore输出0；Fwd不做该mask Cast，暴露AttentionScore输出0、1及drop_mask共三项。所读GE AttentionScore schema的drop_mask却注册为INT8，注释写UINT8，两个子图又分别接FP16/UINT8意图；这组dtype/schema差异需要实际图校验，不能自行统一成某种已支持类型。

mask由常量1生成而非随机采样，keep_prob仍被转交。不能将这套推理mask构造推广成训练dropout等价实现。CreateScalar用模板T的sizeof(T)字节配指定GE dtype，调用ONE的C++ int与UINT8声明也并非相同字节宽度；常量内容拷贝和类型解释由外部GE Tensor合同补核。本次没有导出/编译图验证。

MaskedSoftmaxWithRelPosBias子图固定三个输入，底层schema只有一个y输出，但构图代码`OUTPUT_INDEX=1`选择输出1。这里仅记录源码中的具体不一致，未执行GE验证器，不宣称已复现何种报错或自动修正索引。该schema注释限定Swin结构及相应mask/relative bias广播shape，不能推广成全部LLM注意力。

onnx_common的ChangeFormatFromOnnx只修改Format/OriginFormat descriptor并检查Update返回；它没有执行Transpose/TransData或重排buffer。Vec2Tensor和CreateScalar以原C++存储建立Tensor，标量/向量内存是否复制及生命周期须由实际GE实现确认，不能拿格式标签变化替代物理布局正确性。

## tiling sink的构建与注册边界

common CMake在非RTY kernel配置下构建tiling_sink；开放工程使用ExternalProject，显式选择CANN内aarch64交叉gcc/g++，并要求PRODUCT_SIDE=device。具体输出opmaster按ENABLE_BUILT_IN改名为tiling_device_transformer或cust_opmaster，使用DEVICE_OP_TILING_LIB/BUILT_IN_TILING_SINK宏；开放工程另把DSO复制到构建目录。

sink CMake列出20份Attention cpp依赖，逐一检查EXISTS，缺任意文件即WARNING后return，而非FATAL_ERROR。本次静态路径检查发现这20份cpp均不在固定Main指定目录中，因此不能把外层配置返回成功等同于opmaster已创建或被部署。这里没有运行CMake，也未从别的仓快照补造缺失源。

registry.cpp在非ASCEND_OPTILING_UT时仅注册FusedInferAttentionScore和IncreFlashAttention的DeviceDoOpTiling入口。DeviceOpImplRegistry头只声明map和注册/查找方法，未在本集合给出实现；注册两个symbol不证明两份tiling算法或调度任务完成。device_register库找不到只WARNING；链接是否保留注册资源、DSO是否可装载仍须记录实际产物。

TilingAicpuTask只包含裸TilingContext指针、opType指针、notifyAddr、workspaceAddr/Size；它不是序列化安全、自动同步或自动持有内存的证明。Host/设备地址空间、struct ABI、notify完成协议与workspace寿命需沿真实producer/consumer核对，不能仅凭uint64字段跨进程或跨设备传指针。

## transpose tiling与key编码的调用前约束

GetDataCopyTransposeTiling直接读取src/dst前四维，计算dstHN=dstH/dstN，以及shapeSH、Ns、Nsn、BH等乘积；originalShapeNLen=srcHN*typeSize是字节长度，其他多为元素维度乘积。POD字段为uint32，而输入shape及中间来自int64；没有本地rank>=4、dstN非0、H可整除N或乘积/窄化无溢出检查，也没有填invalidParam/paramsAlign字段。它是tiling字段生成helper，不是实际转置kernel或安全形状验证器。

tiling_key/type两套namespace均以10^19为偏移、低位起十进制RecursiveSum组装Ub轴、block轴、dtype、layout、sparse等枚举。轴NONE=9、布局TND/NTD_TND、SparseEnum不同编码必须沿对应版本解码；大于一位的枚举或负值不能随意追加，否则会串位/转成uint64。编码规则存在不证明相应Device模板注册。

公共tiling_util把scalar shape规范为[1]，IsRegbaseSocVersion只认ASCEND950。它与另一族按DAV_3510/DAV_5102判断的helper不是同一个支持集合；避免把所有Regbase名字当成全仓统一平台门禁。graph/error_codes兼容头优先ge_error_codes，缺时尝试include_next避免混合CANN头递归，否则编译期#error；这表达编译头选择，不保证OpsBase9.2/Metadef9.1运行ABI混搭安全。

## 适配Agent应收集什么

先记录构建开关、导出domain/opset、属性类型/默认值、原节点和生成子图输入输出及常量dtype，再验证mask、非方形长度、动态shape、输出序号和物理layout。之后检查真正DSO、tiling注册symbol、任务ABI和workspace/notify完成协议；正确性通过再分别量转换、常量Fill/Cast、tiling和Device时间。本文未构建、导出、加载插件或运行上游/NPU，没有性能收益及完整Attention Operator结论。
