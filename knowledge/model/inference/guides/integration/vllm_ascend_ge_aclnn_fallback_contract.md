---
type: Guide
title: vLLM Ascend GE到ACLNN公共桥接：描述符、两阶段执行与stub边界
description: 分析固定Main公共fallback的库解析缓存、连续ND与NZ/转置描述符、dtype转换、EXEC_OPAPI_CMD和PREPARE/ExecuteOpLaunch的workspace及句柄寿命，区分真实CANN实现与identity opapi/空tiling stub；指导新增GE fallback及模型算子接入诊断。
aliases:
- fallback::GetOpApiFuncAddr
- fallback::ConvertMmType
- fallback::ExecuteOpLaunch
- fallback::OpApiParams
- EXEC_OPAPI_CMD
- EXEC_OPAPI_PREPARE_CMD
- op::ResizeFrom5D
- RuntimeKb::QueryBank
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/aicpu/cpu_context_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/common/op_api_def.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/common/tensor_util.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/common/tensor_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/cast.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/pad.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/reshape.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/slice.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/transdata.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/transpose.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/fallback/fallback.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/fallback/fallback_2stages.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/fallback/fallback_comm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/fallback/fallback_comm_2stages.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/static/op_resource.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/static/static_space.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/fallback_comm.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/src/fallback_comm_2stages.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/inc/framework/stub_ops.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_api/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_api/aclnn_kernels/common/op_error_check.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_api/level0/ones_like.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_api/opapi_stub.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/op_cache_def_tiling.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/op_cache_tiling.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/op_cache_tiling.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/register/tuning_bank_key_registry.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/register/tuning_tiling_reflection_utils.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/register/tuning_tiling_registry.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/runtime_kb_api.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/runtime_kb_api.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/tbe_tiling_api.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/stub/op_tiling/tbe_tiling_api.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/external/aclnn_kernels/contiguous.h
  role: constraint
created_at: '2026-11-03T05:29:49Z'
updated_at: '2026-11-03T05:29:49Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---
# vLLM Ascend GE到ACLNN公共桥接：描述符、两阶段执行与stub边界

## 先分清桥接层和真实调用者

本文覆盖固定Main `ceac1a2`的`csrc/common`公共GE→ACLNN helper、tensor准备、资源声明和配套stub；它不同于[Torch自定义ACLNN适配层](vllm_ascend_custom_aclnn_binding.md)。对固定csrc的字面检索未找到fallback宏或ExecuteOpLaunch的外部调用/注册点，不能把这些helper存在解释成当前vLLM默认推理管线已启用。新增模型算子要先证明自己的实际caller、注册和编译目标可达。

common CMake在BUILD_OPEN_PROJECT时收集`src/*.cpp`及tiling_base源，否则只收集tiling_base。BUILD_WITH_INSTALLED_DEPENDENCY_CANN_PKG控制子目录扫描；BUILD_OPS_RTY_KERNEL又影响tiling_sink/framework子构建。不能从某个cpp位于源码树推断它进入最终DSO，或把所有构建组合视为等价。

## 库解析是进程状态，不能只看报错库名

`GetOpApiFuncAddr`先尝试libcust_opapi.so，再libopapi.so，最后调用GetAclnnArrdByApiName。dlopen采用RTLD_LAZY，dlsym失败记日志；源码没有在这些路径关闭handle。create/destroy函数、GetWorkspaceSize、执行函数及ResetCacheThreadLocal地址在各调用处静态保存，首次nullptr也不会因后续安装库自动刷新。

拆分aclnn库列表写有infer/train/math/rand/sparse/fft，但for循环内部的`static libHandler`仅初始化一次：实际复用首次迭代得到的handle，而不是每次按当前libName重开。不能宣称已逐一搜索六库；日志中的libName也未必代表本次dlsym的真实handle来源。这是静态代码观察，未运行装载器复现。

两个ACLNN阶段的地址分别搜索，可能来自不同DSO；只按同名symbol配对不能证明ABI一致。诊断应保留首次解析时环境、实际DSO、symbol及提交前版本；先修库/ABI问题，再看kernel数值，不将重试当作地址缓存刷新。

## Tensor转换：重建描述符不等于重排内存

普通`ConvertType(gert::Tensor*)`只使用StorageShape和GetAddr，构造连续stride、offset0、ND格式，并令view/storage shape相同。它没有搬数据或保留原view stride/offset，也不会自动把NZ内存转成ND。传入切片、转置或特殊layout前，应由真实caller保证该描述符与物理buffer一致。

普通GetConvertType列出FP32、BF16、Bool、若干整数、INT4及FP8 E4M3；其余默认为FP16。`ConvertMmType`改走ToAclDataType白名单，未列出的dtype返回ACL_DT_UNDEFINED；这个白名单没有普通路径的FP8 E4M3。两条转换不能互换，既不能将未知dtype默认当正确FP16，也不能从ACL枚举数值一致推断所有dtype支持。

ConvertMmType在rank>1时按StorageShape计算连续stride；transpose交换最后两维的view shape及stride，storage shape与GM地址保持原样。仅enable_NZ且输入primary storage format为FRACTAL_NZ时保留NZ descriptor，否则ND。它只建立转置/NZ视图，不执行Cast、Transpose或TransData。

TensorList逐项创建aclTensor后建列表；子项失败和销毁所有权需按真实CANN实现补核。vector<int64>为空返回nullptr，非空创建IntArray；ConvertScalarType只对float创建Scalar；通用模板原样传递其他C++类型，不自动补optional或数值转换。

## 一阶段宏与拆分prepare/launch的资源合同

| 路径 | 生成与提交 | 清理和边界 |
|---|---|---|
| EXEC_OPAPI_CMD | 要求查询、执行、ResetCacheThreadLocal三符号；reset后转换tuple，调用GetWorkspaceSize；size>0由host_api_ctx分配workspace；取ctx stream执行第二段 | 执行返回后Release转换句柄并FreeWorkspace；无源码级stream完成等待，ctx/ACL的异步内存合同未闭合 |
| EXEC_OPAPI_PREPARE_CMD | new OpApiParams，保存executor/执行函数；Collect参数对应deleter，交SetOpApiParamsWithDefaultDeleter；查询后SetWorkspaceSizes | prepare不提交Device；失败后的vector内指针析构并非由普通vector自动执行deleter，不能假定所有失败路径已清理 |
| ExecuteOpLaunch | 从launch ctx读参数、workspace列表第0项与stream，再调用保存的函数 | 无论执行返回成功/失败都逐项deleter再clear；清理后重放的参数列表为空，executor是否可重用/谁销毁仍由外部合同决定 |

workspace为0的一阶段不会调用MallocWorkspace；两阶段launch却要求workspace sizes/addrs列表都非空，再解引用第0个tensor地址。零字节workspace和“没有workspace条目”必须分别验证。launch只检查op_api_func非空，没有完整检查params及列表子项指针，调用方不能依赖它兜底任意坏ctx。

宏用转换tuple的实际C++类型reinterpret_cast查询函数原型，参数位置、标量位宽、可选空值和输出指针必须与目标ABI逐一对应。句柄Release对Tensor/Scalar/IntArray/BoolArray/TensorList有销毁重载，其他类型为空操作；floatArray也没有对应Release重载。裸aclTensor*直接透传后仍会进入相同Release，借用/新建对象归属需要caller明确。

头中ConvertedParams提供move-only RAII，但上述宏使用普通tuple，不能因RAII类存在就宣称宏所有异常/早退均安全。查询失败或workspace分配失败时，普通宏还没进入其显式Release路径；两阶段的框架默认deleter是否遍历OpApiAnyValue也未在本集合证明。这里未测得泄漏/UAF，不将静态缺口写成已复现故障。

## 通用tensor准备会增加实际计算节点

`ResizeFrom1D`先Contiguous、Cast FP32，再对通道向量Unsqueeze成NCHW/NCDHW；不支持NCDHW时走TransDataSpecial。ResizeTo1D执行相反的格式/维度操作，Cast回输出dtype并ViewCopy。ResizeFromND只取前4维、不足补1，没有任意高rank通用折叠证明。

ResizeFrom5D明确先按[0,2,1,3,4]把NCDHW换为NDCHW，再把N*D并成4D；ResizeTo5D按原输入shape reshape回并做逆Transpose。这不同于只ReFormat修改标签。FillScalar/FillVector先构造shape和值tensor再Fill；ProcessEmptyTensorWithValue仍需实际Fill和ViewCopy，不能把名字Empty理解成无需执行。

external头只给接口和前置条件：Reshape要求连续且最多一个-1；TransData与TransDataSpecial对FP32/INT32的c0约定不同，bool特殊路线要求先Cast再格式转换。实现属于实际链接的CANN库，这些声明不证明无拷贝、零workspace或任意stride支持。

CombineCategories优先保留已经是浮点的higher，lower浮点或higher为Bool时才走PromoteType，higher非UNDEFINED时也可能直接保留。它不是一般意义上每对dtype都对称的最大精度规则。公共op_api_def中的精度枚举只是KEEP/ALLOW_DOWN_PRECISION/FP16/HF32等参数值，不能当作硬件自动选型或误差保证。

## stub可以满足链接，但不提供数学正确性

op_api CMake构建opapi_math，ENABLE_TEST时另构建opapi_stub；二者当前都从相同stub cpp收集源，使用旧C++ ABI宏。必须沿最终链接和装载确认真实实现，不能只按库名是否含stub判断。

opapi_stub里的Cast、Contiguous、ViewCopy、Reshape、Slice、TransData、Transpose、多种加乘/归约/收集及ZerosLike等直接返回输入；Fill返回value，Sort返回同一self的两份指针，CanOptimizeContiguous/View恒true。这不会执行dtype/layout转换、输出回写、排序或零填充。通过这种实现的测试只能证明对应控制流程，不是模型精度或内存布局证据。

optiling stub中GenTiling、TilingPrepare、GetTbeTiling直接返回true且不写输出，QueryBank返回0且不填写tiling对象。CacheTilingData虽大量字段默认1/0，tiling_id未默认初始化；某返回值“成功”不证明拿到了有效tile。Conv3D POD和一组level0函数声明也不补足其设备算法。

tuning bank V1宏的Parse/Load始终false；V2宏才按sizeof(bank_key)检查并用JSON序列化/反序列化，异常返回false。反射FromJson对缺字段/unique_ptr optional直接跳过，新增字段可能保留旧值或未初始化值，不能当作严格完整schema校验。TUNING_TILING_DATA_FIELD_DEF生成字段时本身不初始化；factory声明不是实际Runtime KB命中结果。

op_error_check按调用点检查null、dtype、broadcast和rank；其CheckDims只排除单维大于INT32_MAX，不证明维度非负、总元素乘积无溢出或实际buffer容量。CheckReduceOutShape允许两边元素数均为1时shape不同。ones_like的IsAiCpuSupport也只查dtype白名单，没有提供OnesLike设备实现或真实AICPU分派。

stub_ops仅注册Data/Const/Cast/Fill的schema。Cast schema列出的低精度类型很广，但不能与identity stub组合推断FP8/FP4真实计算支持。已全文结构审查的纯level0声明及与external逐字节相同的stub头，在来源表按声明/重复skip保留，未当成未读Device算法跳过。

## 资源注册与新模型验证顺序

StaticSpaceInitializer在默认space不存在时创建registry；EXTERN/AUTO_GEN_OP_RESOURCE只声明/聚合tiling、infer、tuning和binary资源，不证明资源已经注册并能运行。AICPU GetAttrValue必选属性缺失返回false；Opt变体缺失保持传入值不动，caller应在调用前给确定默认值，不能假定它替自己初始化。

新增GE fallback时，先记录构建flag、实际caller/registry及最终DSO，再核验两阶段ABI、dtype和descriptor布局。然后验证查询失败、零/非零workspace、参数/列表所有权、执行失败、多stream及图重放；对所有Cast/Transpose/Fill等准备节点确认实际执行，而不是identity stub。正确性通过后再比较转换、查询/prepare、launch及Device时间。本次只读固定源码，未装载DSO、编译、运行上游或NPU，不提供性能收益或完整Operator结论。
