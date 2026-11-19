---
type: Guide
title: ATB分页注意力执行：描述符、Operation缓存与工作区
description: 沿PA和MLA入口核对完整bridge类型转换、输入准备、Operation缓存、捕获分派、Setup及显式工作区边界。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionMlaAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionMlaAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp
  role: implementation
created_at: '2026-11-10T15:02:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ATB分页注意力执行：描述符、Operation缓存与工作区

## 固定准确入口与已有知识

本卡核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的atb命名空间`_npu_paged_attention`、`_npu_paged_attention_get_workspace`、`_npu_paged_attention_mla`及所列公共消费者。入口以TORCH_LIBRARY_FRAGMENT(atb)声明、PrivateUse1实现注册；不把它们当作[npu_fused_infer_attention_score](../apis/torch_npu/npu_fused_infer_attention_score.md)或其他ACLNN/FIA分支。

[LibTorch部署入口](bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)已有ATB导出库和命名空间说明，本卡补实际执行准备，不能从头文件、库名或dtype映射表认证产品能力。平台、完整ATB库及软件配套未知，保持draft、空平台；未导入、编译、注册运行或进行设备实验。

## 普通分页与MLA共享参数缓存，但输入槽不同

普通分页入口、workspace getter与MLA入口均以query建立OptionalDeviceGuard并构造PagedAttentionParam。它们使用下列完整共同赋值；字段在所读包装中固定，不能从参数类型或普通PA可用推导其它mask、量化或压缩组合也可用。

| 参数字段 | 本地赋值 |
| --- | --- |
| headNum / kvHeadNum / qkScale | num_heads / num_kv_heads / scale_value |
| maskType / batchRunStatusEnable | UNDEFINED / False |
| quantType / outDataType / hasQuantOffset | TYPE_QUANT_UNDEFINED / ACL_DT_UNDEFINED / False |
| compressType / calcType / scaleType | COMPRESS_TYPE_UNDEFINED / CALC_TYPE_UNDEFINED / SCALE_TYPE_TOR |
| inputLayout | TYPE_BSND |

普通分页及其getter另固定mlaVHeadSize=0，输入依次为query/key_cache/value_cache/block_table/context_lens；MLA把mla_vheadsize显式转uint32赋给该字段，只有query/key_cache/block_table/context_lens，没有value_cache输入槽。getter和普通执行入口的全部scalar属性、输入顺序/格式标志与out描述准备一致；它通过Setup取所需量而不调用Execute。

准确schema中普通入口的workspace是关键字Optional Tensor，默认None；MLA schema没有此参数，二者写Tensor(a!) out并返回()。getter的out也标Tensor(a!)，但返回的是按query.options申请的Byte workspace Tensor，而不是把out作为Attention结果返回。这是本地schema/调用行为，不能由别名标记推导Setup已计算输出。

query、block_table和context_lens的Input调用显式传format_trans=True；Cache使用缺省False。输出直接使用调用者给定out，入口自身不另申请Attention输出，Schema标Tensor(a!) out且返回()。不能因为函数不返回Tensor就忽略out写入，也不能把MLA省value_cache解释成任意Cache shape等价。

这些局部属性赋值和uint32转换没有建立所有head/shape/值域合法性。不能把TYPE_BSND枚举、PrivateUse1注册或普通分页可用推导成全部MLA组合受支持。

## ParamSetter会准备数据，Output不会自动连续化

每个已定义Input先调用tensor.contiguous；需要format_trans时，再通过FormatTrans把NPU对象请求转为ND，CPU对象原样保留。随后CPU输入再clone并保存到cpu_tensors；NPU输入对象保存到contiguous_tensors。已有连续输入的contiguous调用不意味着每次必复制，ND转换也应按真实格式核成本；这些不是把NPU输入统一转CPU的路径。

AtTensor2AtbTensor要求对象连续，使用data_ptr设置CPU hostData或非CPU deviceData，以sizes填shape、经格式helper及dtype_map构造描述符。基础NPU格式被描述为ND，其他内部格式保留；该映射不认证算子接受表中每种dtype。主线另外检查dim<=atb::MAX_DIM，发布所读转换没有这一检查，其余所选Common.cpp token差异仅此新增检查。

Output直接调用同一描述符转换，不先contiguous、clone或按目标shape重新分配。因此调用者需要按准确接口提供out，不能把Input的准备规则套给输出，或从未在入口遍历shape就推定任意输出缓冲合法。


## bridge的完整dtype映射和dataSize

AtTensor2AtbTensor使用下表将ATen ScalarType写入ATB描述符。此表属于bridge转换合同，具体Attention操作的可接受dtype仍按各自参数和产品条件核对。

| ATen ScalarType | aclDataType |
| --- | --- |
| Bool | ACL_BOOL |
| Byte | ACL_UINT8 |
| Char | ACL_INT8 |
| Half | ACL_FLOAT16 |
| Float | ACL_FLOAT |
| Int | ACL_INT32 |
| Long | ACL_INT64 |
| BFloat16 | ACL_BF16 |
| Double | ACL_DOUBLE |
| Short | ACL_INT16 |
| ComplexHalf | ACL_COMPLEX32 |
| ComplexFloat | ACL_COMPLEX64 |
| ComplexDouble | ACL_COMPLEX128 |

转换函数先检查连续性（主线还检查dim≤MAX_DIM），设置format、CPU hostData或非CPU deviceData，再以sizes填写shape。查dtype_map未命中时TORCH_CHECK拒绝；命中才写入desc.dtype。最终dataSize直接委托`atb::Utils::GetTensorSize(tensor)`，其结果应与真实ATB格式和描述符一起核对，不能在包装层仅按逻辑numel替代。

Tensor Input重载收到undefined Tensor时，会先压入空atb::Tensor并返回；Optional Input重载收到None也压入空描述槽。两条分支均保留该位置，已定义输入才继续contiguous、可选格式准备及CPU clone/NPU对象持有。Output沿已述转换函数直接处理调用方对象。

## Operation缓存不等于结果或工作区缓存

OpParamCache<PagedAttentionParam>实例为thread_local。所读getOperation在捕获状态整数为非零时直接CreateOperation，不进入普通参数缓存；否则computeHash后用uint64键查op_map，命中返回Operation指针，未命中创建并保存。普通缓存析构遍历DestroyOperation；不能把捕获新建对象误写成每次都会命中原对象。

所选PagedAttention参数hash纳入kvHeadNum、headNum、qkScale、quantType、outDataType、mlaVHeadSize、maskType、calcType，没有把当前Tensor内容、全部shape或workspace对象放入这个特化。查表处也没有第二次完整参数相等比较。这里只记录固定键和复用范围，不声称存在已复现碰撞，也不认证任意跨设备、跨线程或动态shape的复用正确性。

ContextManager则在所读实现中使用单例和call_once创建Context，每次GetContext再SetExecuteStream到传入流，不是按流创建一张独立Context表。不能由Operation实例thread_local就推导Context和所有资源也隔离，或推定并发/跨设备安全。

## 捕获分派改变Setup和workspace准备阶段

| 所查公共路径 | 可直接确认的阶段 |
| --- | --- |
| 捕获状态非零的RunAtbCmdV1 | 调用线程以current stream(false)取得Context并Setup；需要时用PrivateUse1、Byte empty申请workspace，再将VariantPack、裸workspace地址/字节数、Context、op和cpu_tensors交给RunOpApiV2回调。 |
| 非捕获的RunAtbCmdV2 | 先取得stream并复制VariantPack；回调内部再GetContext、Setup，workspace非零时调用allocate_workspace(workspace_size,stream)，然后Execute。 |

两路每次都经过OperationSetup，它检查Setup status==0；参数缓存命中不免除这个步骤，也不是workspace长期复用保证。V1回调返回Execute状态并调用DestroyOperation；V2读取Execute返回值st后局部返回0。该差异只描述此回调如何传状态，不扩为全部异步错误都被吞、全部异常都安全清理或数值正确。

所见回调显式值捕获cpu_tensors，未把ParamSetter的contiguous_tensors以相同方式列入捕获。VariantPack及workspace仍携带裸地址；本卡未展开底层队列、分配器记录和异步资源寿命，不能只凭局部maintainer或缓存对象存在就认证所有临时NPU缓冲一直有效，也没有复现资源失效。

## 显式workspace需区分所需字节和提供字节

普通分页入口仅在workspace有值且defined时走RunAtbCmdWithWorkspace，否则走自动分配；MLA所查签名没有workspace参数，走自动路径。get_workspace使用同一组普通分页参数/槽位，Setup得到workspace_size后按query.options、Byte申请该长度的Tensor；本函数没有Execute，不能把返回workspace或给定out当作已算出Attention结果。

带workspace两路仍做OperationSetup，把返回所需量存为fake_workspace_size；实际Execute的容量则取`workspace.numel()*workspace.element_size()`。所读函数没有比较提供容量是否至少达到Setup要求，没有在此校验workspace的dtype、device或连续性。调用使用storage().data作地址，没有显式加storage_offset；不能仅凭Tensor numel或任意子view推定传入的是预期可写区域。

这些是包装薄层的局部边界，底层ATB仍可能另行拒绝或检查，本次没有构造不足工作区、切片或跨设备输入执行。调用者应保留与准确shape/参数一致的所需字节、实际容量和整块地址合同，不能用其他FIA接口的workspace规则替代。

## Utils的完整转换表、格式与Context销毁

Utils.h的kATenScalarTypeToAclDataTypeTable与前述Common.cpp的unordered dtype_map是两套消费者；不能因13个有效映射同名就把代码路径合并。前者按ScalarType的整数值直接下标取表，再对ACL_DT_UNDEFINED作TORCH_CHECK，没有额外的下标范围或未来枚举序列一致性校验。有效项为Byte/Char/Short/Int/Long/Half/Float/Double/ComplexHalf/ComplexFloat/ComplexDouble/Bool/BFloat16，分别映射到UINT8/INT8/INT16/INT32/INT64/FLOAT16/FLOAT/DOUBLE/COMPLEX32/COMPLEX64/COMPLEX128/BOOL/BF16。其宏还将QInt8、QUInt8、QInt32、QUInt4x2、QUInt2x4、Bits1x8/Bits2x4/Bits4x2/Bits8/Bits16、Float8_e5m2/Float8_e4m3fn、Undefined和NumOptions显式设为ACL_DT_UNDEFINED；ConvertToAclDataType不将这些项当成已支持量化或Float8。

FormatTrans只对is_npu为真的Tensor请求npu_format_cast(ND)，其他设备原样返回。GetFormatForAtb对非NPU直接返回ND；对NPU查询实际格式，并将NCHW、ND、NHWC、NCDHW四个基础格式记为ND，其余格式保留。这是描述/准备规则，不证明其他设备可供ATB执行或内部格式受具体算子接受。

ContextManager构造置nullptr，禁止复制/赋值；单例GetInstance为函数局部static。GetContext用once_flag/call_once创建并检查status==0，随后每次SetExecuteStream；本地没有围绕这个流设置另加锁或按设备/流分表。析构仅在指针非空时DestroyContext、检查返回0，再置nullptr；失败检查的存在不是所有退出路径都完成清理的证明。get_op_mode模板将Optional字符串value_or到默认键，map.find未中即报Unsupported，返回的是登记整数，没有跨字段组合校验。

## 完整Operation缓存接口与参数键家族

CreateAtbOperation调用CreateOperation后只检查op指针非空，未把该调用返回状态另赋值检查。OpParamCache每种ParamType的getInstance为thread_local，禁止复制/赋值；构造先取ContextManager单例以表达销毁次序意图。析构对map中每个指针调用DestroyOperation，不在此检查销毁返回码；没有额外LRU、容量上限或自动淘汰。

getOperation(param,name)在捕获非零时绕过map新建，普通路径才computeHash后按单个uint64键命中/创建。另一重载getOperation(hash_id)只是查询，缺失返回nullptr，不创建也不按捕获状态分派；saveOperation直接赋op_map_[hash_id]=op，即便nullptr也没有单独拒绝。覆盖旧值没有在这个方法里先Destroy旧指针。两接口不能因同名被描述为相同创建/生命周期合同；map命中没有二次完整参数相等比较。

OperationCacheCompute.h的默认HashOpParam<T>不写字段，下面六种特化才按所列顺序写“字段标签字符串+字段值”。模板computeHash(obj)每次先将TLS偏移清0，再调用对应特化；未特化类型不是自动序列化全部结构体。

| 特化 | 顺序字段（标签可与成员名不同） |
| --- | --- |
| RmsNormParam | epsilon=normParam.epsilon、layerType、quantType=normParam.quantType |
| GroupTopkParam | groupNum、k、groupMultiFlag、n |
| PagedAttentionParam | num_kv_heads=kvHeadNum、num_heads=headNum、scale_value=qkScale、quant_type=quantType、outdata_type=outDataType、mla_vheadsize=mlaVHeadSize、maskType、calcType |
| SelfAttentionParam | num_kv_heads=kvHeadNum、num_heads=headNum、scale_value=qkScale、calcType、kernelType、maskType、quantType、isTriuMask |
| RopeParam | rotaryCoeff |
| ReshapeAndCacheParam | compressType、kvCacheCfg |

该表只说明现有缓存键选项，不补全结构体所有其他字段，也不把HashOpParam默认空实现称作对任意可变参数安全。各算子本地固定字段、可变参数和厂商条件仍按对应指南核对。

## 原始字节序列化、8192边界与完整hash实现

另一computeHash(name,args...)先清TLS偏移，再序列化名字及各参数。std::string只写s.size个字节，不写长度或终止NUL；普通模板写对象地址的sizeof(T)个原始字节。Tensor和Optional Tensor重载完全不写，空参数重载无动作；没有通用的Tensor shape/stride/值序列化。泛型对象也不因此获得跨版本、进程或指针寿命稳定的语义编码；此处不声称已复现任何冲突。

缓冲g_hash_buf为TLS的8192字节，g_hash_offset也为TLS。MEMCPY_TO_BUF在“偏移+本次大小>8192”时把偏移设为9216并从当前add函数返回，不写该片段；calc_hash_id在偏移恰为这个哨兵时返回0，否则对当前缓冲和偏移计算。计算开头会重置偏移，但没有在这里清零整个缓冲。缓存getOperation(hash_id)/saveOperation没有把0当作自动绕过缓存的特殊键；不能把溢出回0误写成该层已禁用复用。

完整gen_hash使用默认seed 0xdeadb0d7、两个64位累加器，每16字节处理两块64位数据，经乘固定常量、rotate-left和交叉累加；尾部按len&15用fallthrough拼入t1/t2，再合入长度、交叉累加、mixture的33位xor/乘混合，最终返回第二累加器hax。rotating_left只是移位或，mixture用本文件两常量作最终混合；这不是加密身份、无碰撞证明或可持久化协议。算法与完整缓存键/转换宏的来源版本一起核验，不从hash函数存在推导任何Tensor布局、工作区或设备执行都安全。

## 版本对照与优化入口

两版分页/MLA入口、Utils.cpp、OperationCreate.h和参数hash文件的完整非注释token分别相同；Common.cpp仅新增上述维数检查。本卡对AtbCommon.h仍绑定Evidence所列TensorMaintainer和ParamSetter声明；完整动态转换/dispatch宏及其lookup版本差异见[MLA准备指南](torch_npu_atb_mla_preprocess_and_ring_preparation.md)的补充，不把声明与动态库实现合并。

定位首调/稳态成本时分开记录输入contiguous/ND准备、CPU clone、Operation创建/命中、每次Setup、自动或显式workspace，以及Execute和out写入；记录是否捕获、准确流和软件版本。先验证数值、输出别名与资源寿命，再比较性能。本次没有运行ATB、设备、捕获、并发或性能测试，不新增verified或耗时数字。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionAtb.cpp)（primary）：19–119。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionAtb.cpp)（implementation）：19–104。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedAttentionMlaAtb.cpp)（implementation）：19–70。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedAttentionMlaAtb.cpp)（implementation）：19–67。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：16–215。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.cpp)（implementation）：16–207。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.cpp)（implementation）：完整本地文件1–75。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.cpp)（implementation）：完整本地文件1–85。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：完整本地文件1–114。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：完整本地文件1–124。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：91–95,559–574。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：90–93,508–521。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：完整本地文件1–158。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：完整本地文件1–167。
- [固定补充来源 Utils.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：完整本地文件1–95。
- [固定补充来源 OperationCacheCompute.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp)（implementation）：完整本地文件1–195。
- [固定补充来源 Utils.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：完整本地文件1–95。
- [固定补充来源 OperationCacheCompute.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp)（implementation）：完整本地文件1–187。
