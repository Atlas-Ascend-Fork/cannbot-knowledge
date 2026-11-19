---
type: Guide
title: ATB MLA准备：固定输出、Cache格式与Ring统计
description: 聚合MLA预处理和Ring MLA的输出分配、模式默认值、CPU长度要求与执行宏消费者，区分Cache输出和输入别名。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/MLAPreprocessAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/MLAPreprocessAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/RingMlaAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/RingMlaAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h
  role: implementation
created_at: '2026-11-10T15:12:29Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# ATB MLA准备：固定输出、Cache格式与Ring统计

## 固定准确入口与复用范围

本卡核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的`atb::npu_mla_preprocess`、`atb::npu_ring_mla`及各自out入口。两版入口以TORCH_LIBRARY_FRAGMENT(atb)声明并注册PrivateUse1；不是[npu_mla_prolog](../apis/torch_npu/npu_mla_prolog.md)系列或FIA的同名替代。平台与完整ATB配套未知，保持draft、空平台；未导入、编译、注册执行上游或运行设备。

[ATB分页注意力生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)已覆盖PagedAttentionParam、ParamSetter和RunAtbCmd路线。本卡改用EXEC_ATB_CMD动态接口宏，不把ParamSetter的ND转换/CPU clone规则照搬；本卡聚合MLA前置准备及Ring计算所需状态，不逐接口重复缓存和支持表。

## MLA预处理的输入分组与完整调用顺序

两个MLA预处理重载都以input建立OptionalDeviceGuard。schema的16个位置Tensor依次为input、gamma0、beta0、wdqkv、descale0、gamma1、beta1、wuq、descale1、gamma2、cos、sin、wuk、kv_cache、kv_cache_rope、slotmapping。关键字quant_scale0/quant_offset0/bias0、quant_scale1/quant_offset1/bias1、ctkv_scale/q_nope_scale这8项均是默认None的Optional Tensor；cache_mode与quant_mode是默认None的Optional字符串，随后按各自map选默认值。

传给AtbMLAPreprocess的实际顺序会将这些可选参数插入各投影组，不能把schema位置Tensor顺序直接作为动态接口参数顺序。以下编号从接口名之后的第一个实参起算，两重载相同：

| 实参序号 | 固定顺序 |
| --- | --- |
| 1–8 | input、gamma0、beta0、quant_scale0、quant_offset0、wdqkv、descale0、bias0 |
| 9–15 | gamma1、beta1、quant_scale1、quant_offset1、wuq、descale1、bias1 |
| 16–24 | gamma2、cos、sin、wuk、kv_cache、kv_cache_rope、slotmapping、ctkv_scale、q_nope_scale |
| 25–35 | wdq_dim、q_rope_dim、k_rope_dim、epsilon、q_rotary_coeff、k_rotary_coeff、transpose_wdq、transpose_wuq、transpose_wuk、cache_mode、quant_mode |
| 36–39 | q_out0、kv_cache_out0、q_out1、kv_cache_out1 |

这些Optional Tensor由包装原样传入宏，没有在本地根据名称自动生成scale/offset/bias、推导所选量化组合合法，或填入dummy Tensor。动态转换的None与已定义对象边界应按所配接口核验，不把另一路ParamSetter的空atb::Tensor槽照搬到此宏ABI。

三个维度变量为uint32的0，epsilon为float 1e-5，两个rotary_coeff为uint32的2，三个transpose标志为True，全部在调用前固定；底层意义仍保留下文的证据边界。普通重载把input.size(0)和wuk.size(0)存入C++ int token_num/head_num，再申请输出；本地没有为这种窄化另做范围检查。模式解析及Cache输出分配的实际先后见下文。

## MLA预处理的四输出与固定维度

无out入口从input.size(0)取token_num、wuk.size(0)取head_num，按以下顺序申请和返回：

| 输出 | 局部申请依据 |
| --- | --- |
| q_out0 | `(token_num,head_num,512)`，options取kv_cache，不能一律按input dtype估算。 |
| kv_cache_out0 | 与kv_cache同逻辑shape/options；cache mode为2或3时请求FRACTAL_NZ，否则普通empty。 |
| q_out1 | `(token_num,head_num,64)`，options取input。 |
| kv_cache_out1 | 与kv_cache_rope同逻辑shape/options；同样仅mode2/3请求FRACTAL_NZ。 |

512/64是所读包装的固定尾维，不是对任意MLA head dimension的能力认证；token/head由对应轴直接取值，也没有在这里完整校验所有投影权重、RoPE或Cache尺寸相互一致。Cache输出是新申请对象，所读包装没有把它们直接返回为输入Cache的别名。

普通Schema没有为输入kv_cache/kv_cache_rope标突变别名；out Schema则分别给四个提供的输出标a!/b!/c!/d!，函数返回它们的引用。它没有复制无out分配逻辑去resize或检查这些out，不能据名字认定能省略返回Cache、Cache输入一定原地更新或底层绝不改输入。实际状态更新与存储别名需精确消费者/底层合同。

## 模式名不替代dtype或物理布局转换

MLA cache_mode仅按精确map接受krope_ctkv→1（默认）、int8_nzcache→2、nzcache→3；quant_mode接受per_tensor_quant_asymm→0、per_token_quant_symm→1（默认）。get_op_mode以optional默认值查表，未命中报错，没有在此做大小写归一或任意字符串兼容。

模式2/3控制的是上述Cache输出的NZ申请，没有因int8_nzcache这个名字就显式把所有Cache/Q输入输出转INT8。给定Cache的options仍参与输出dtype；所读函数也没有先把权重按某个物理打包协议重新排列。不能把mode名、contiguous或普通transpose视图当成完成NZ量化/布局转换。

两重载向AtbMLAPreprocess固定传wdq_dim/q_rope_dim/k_rope_dim=0、epsilon=1e-5、两个rotary_coeff=2、三个transpose权重标志=True。0的底层含义和内部推形没有在本卡展开，不能把它解释成输出尾维为0或所有维度自动兼容。无out在解析模式前已申请两份Q输出，非法模式报错不代表此前没有准备工作。

## Ring MLA的统计顺序和CPU长度

Ring无out从q_nope.size(0)取q_ntokens、value.size(2)取head_size_v，申请output形状`(q_ntokens,head_num,head_size_v)`且options取q_nope；另申请FP32 softmax_lse，形状`(head_num,q_ntokens)`。LSE的轴序不能交换，也不能从它为FP32推定output或所有内部累加也为FP32。

qk_scale显式转float后传给AtbRingMLA；两重载默认kernel_type_high_precision→1、no_mask→0、type_bsnd→0、calc_type_first_ring→1。其他已列键为kernel_type_default→0、mask_type_triu→1、calc_type_default→0，布局map只有type_bsnd。high_precision名称本身不认证某种累加算法或数值误差界。

两重载都先seqlen.clone，再明确检查克隆对象在CPU；没有自动把NPU seqlen迁移到CPU。无out的output/LSE申请和模式解析又早于这个检查，不能以最后报CPU要求推定前面没申请。pre_out和prev_lse可选项原样交宏，所读入口没有补零或完整校验二者配对、shape/dtype与calc_type的组合；不能仅凭默认first_ring就推导任意缺失/历史状态安全。

Ring out不在本地重建output/LSE形状或强制LSE dtype，直接传提供对象并返回两引用。按无out的形状准备它们只是局部分配线索，不能代替目标ATB算子对所有布局和模式的完整合同。

## Ring输入、历史状态和宏实参顺序

两个Ring重载均以q_nope建立OptionalDeviceGuard。schema位置输入为q_nope/q_rope/k_nope/k_rope/value/mask/seqlen/head_num/kv_head_num；mask在此是必传Tensor。关键字pre_out/prev_lse均默认None，qk_scale默认1，四个模式字符串默认None；out重载再提供Tensor(a!) output及Tensor(b!) softmax_lse，并返回两引用。没有因名字相似就把pre_out和prev_lse合并或互换。

get_ring_mode以kernel、mask、layout、calc顺序逐项get_op_mode并返回四int tuple，调用者按同样顺序std::get。map精确键和值以及各默认值沿上一节记录，helper没有额外做模式之间或历史状态shape的交叉合法性检查。

传给AtbRingMLA的完整18实参依次为q_nope、q_rope、k_nope、k_rope、value、mask、seqlen_clone、pre_out、prev_lse、head_num、kv_head_num、qkScale_float、kernel_type、mask_type、input_layout、calc_type、output、softmax_lse。两重载都把double qk_scale转float、clone seqlen并检查CPU；不存在自动把设备长度迁移到CPU的本地分支。对18项原始值和两输出作准确记录，才能核对每一环的状态合并与工作区需求，不能用单个模式名替代该合同。

## EXEC_ATB_CMD不是ParamSetter的另一种拼写

两版所选宏按捕获状态整数非零选V1，否则V2；不是按TASK_QUEUE_ENABLE的0/1/2来命名分支。两路都缓存查询执行符号与GetWorkspaceSize符号并检查非空，仍不构成设备、dtype或shape支持认证。

V1用ConvertTypes为Tensor构造aclTensor：先contiguous，再记录实际format、sizes、strides、storage_offset和Storage地址；可选未定义项变nullptr。非捕获V2先CopyTypesV2，保存同类描述信息到TensorStruct，再在回调中ConvertTypesV2构造aclTensor。这里没有ParamSetter那个format_trans=True参数，也没有其CPU输入必经clone的同一路分支；Ring的seqlen clone来自入口自身。

这些转换同样作用于作为宏实参提供的输出Tensor。所读out包装没有CheckOut或显式format_fresh_view回写；不能只因Schema标了突变别名就认证任意非连续out写回原对象已经核验。本卡记录调用链，未复现写回错误，也未展开全部底层别名和异步缓冲寿命。

## 参数hash、workspace及失败状态的消费者

V1在调用线程查询workspace/Operation，需要时以PrivateUse1 Byte empty申请，回调执行后检查返回状态，再DestroyOperation及ReleaseConvertTypes。V2则在回调中取Context、查OpParamCache<uint64_t>，调用GetWorkspaceSize后saveOperation；这个保存发生在workspace_status检查之前，不能把缓存项存在当作Setup已成功。

V2仍每次调用workspace查询，workspace非零时在回调中allocate_workspace，随后执行并检查状态、释放转换的描述符；缓存Operation不等于缓存workspace或有效MLA结果。两路的显式释放都受前面检查/异常顺序影响，不据这些行认证所有失败路径完成清理。完整Context、分配器和队列寿命范围继续按前卡边界核验。

V2在入回调前用接口名和宏参数计算hash；所读Tensor及optional Tensor的add_param_to_buf重载为空，非Tensor参数和名字走相应序列化。不能把当前Tensor内容、shape/stride或Cache值变化当成一定导致该hash失配，也不据局部键省略推断任意动态shape均可复用或存在已复现碰撞。它与前卡PagedAttentionParam八字段的专用hash是不同消费者。

## 完整动态符号查找与版本失败分支

AtbCommon.h按顺序尝试静态保存的libatb.so句柄及libopapi.so句柄，dlopen使用RTLD_LAZY；失败只告警，dlsym未中也只在该helper告警。第一库找到符号即返回，否则尝试第二库；第二库成功加载但仍找不到符号才TORCH_CHECK。静态句柄首次为nullptr后，本函数没有每次重试dlopen的分支；不由“可回退第二库”推出运行环境任意缺库都可恢复。

主线在最后显式return nullptr：两次加载都未能返回符号、且第二库句柄为空时会到这里。发布同函数末尾没有这句return，不能将其描述为同样保证返回nullptr的失败合同。GET_OP_API_FUNC仅按类型别名reinterpret_cast，不能以该宏名代替实际符号是否存在或ABI匹配验证。

## 完整aclTensor转换、元数据副本和释放范围

MAX_DIM_NUM=5与N=32用于SmallVector的内联容量，不是本头对Tensor秩或参数数量执行的上限检查；两个转换函数里的dimNum局部值没有参加后续检查。直接Tensor ConvertType首先静态查询aclCreateTensor，符号为空返回nullptr，undefined Tensor也返回nullptr；已定义Tensor先contiguous，再经实际格式与dtype helper准备。格式/ScalarType表的完整边界见[执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)。

aclCreateTensor接收逻辑sizes、strides、storage_offset及原始storage().data。非ACL_STRING时要求itemsize>0，storage_dims只有一个nbytes/itemsize元素，表示底层Storage容量，不用逻辑numel代替；ACL_STRING分支保持storage_dims为空，不能由这个分支推导前述dtype表已经接受String。CPU对象保存到maintainer.cpu_tensors，其余到contiguous_tensors；这里没有ParamSetter对CPU再clone的步骤。Optional Tensor仅在has_value且defined时递归，其他为nullptr；普通泛型ConvertType按值原样返回，ConvertTypes用make_tuple逐项处理，没有额外生成数值或解析字符串。

非捕获先CopyTypeV2：TensorStruct保存data_ptr、scalar_type、nbytes、itemsize、storage_offset、sizes/strides的独立vector及format；TensorStructPtr持有这些元数据，原Tensor仍由两个maintainer列表分别持有。共享元数据指针本身不是拥有原始Storage的替代物。Optional/undefined同样为空，泛型仍按值透传；CopyTypesV2逐项组tuple。回调内ConvertTypeV2(TensorStructPtr)按同一Storage/offset/格式规则创建aclTensor，ConvertTypesV2最后额外拼workspace_size指针、Operation**和Context*。

call通过index_sequence展开tuple；ConvertToOpApiFunc用各实参的decay类型组成int返回函数指针，再reinterpret_cast符号地址。本头没有基于远端声明自动核验动态函数完整签名。非Tensor泛型按值复制也不等于深拷贝其可能引用的外部数据。

Release(aclTensor*)静态取aclDestroyTensor，缺符号即返回，否则调用而不检查销毁状态；Release(Context*)为空，泛型Release只丢弃值。ReleaseConvertTypes用initializer_list逐tuple项调用这些重载，不销毁泛型Operation*、Context或底层Tensor Storage。执行宏里显式DestroyOperation与描述符Release是不同步骤；不能把调用ReleaseConvertTypes概括为释放所有资源。

## 显式workspace和最大查询宏的完整控制流

普通EXEC_ATB_CMD在捕获非零走V1，否则V2，既有章节描述执行与保存顺序。两种显式workspace内部宏在源码中拼作WTIH_WORKSPACE_V1/V2，公共WITH_WORKSPACE分派到它们。V1仍在调用线程转换、取Context、查询workspace与Operation；V2仍先复制参数/hash，在回调取Context、查缓存、转换和查询，并在workspace_status检查前saveOperation。二者都先查询所需字节到fake_workspace_size，但实际执行只取给定workspace.storage().data及numel×element_size，没有本地将二者比较，也未加storage_offset或新增dtype/device/连续性校验。

普通V1自动工作区为PrivateUse1 Byte empty，V2在回调用allocate_workspace(workspace_size,acl_stream)；显式两路不另申请这块workspace。四个执行宏在查询和执行状态检查之后才走既有DestroyOperation/Release分支，异常前后次序不同，不提供所有错误路径RAII清理保证。它们按值捕获cpu_tensors；contiguous_tensors或workspace Tensor对象没有以相同名字进入相应lambda捕获，只能按实际回调/分配器/队列合同进一步核验寿命，不能仅由TensorStructPtr认定全部设备临时对象被持有。

EXEC_GET_ATB_MAX_WORKSPACE_CMD是直接调用的泛型lambda，不经RunOpApiV2排队；它仍静态查询并要求GetWorkspaceSize和执行符号两者非空，即便本次不会Execute。先CopyTypesV2/hash、取当前流Context，再查OpParamCache<uint64_t>、ConvertTypesV2、调用查询、saveOperation，随后才检查workspace_status并返回字节数。atbName和api_ret局部没有参与这段返回选择。该宏本体没有Execute、没有给调用者分配Byte Tensor、没有Destroy缓存Operation，也没有ReleaseConvertTypes成功路径调用；不能把其他执行宏的描述符清理自动套给它。相关包装getter如何按返回字节申请Tensor，应逐接口看本地实现。

本头末尾的AtTensor2AtbTensor、GetContext、ParamSetter及RunAtbCmd/GetAtbWorkspaceSizeCmd/RunAtbCmdWithWorkspace是声明；前卡已按实际Common.cpp定义解释可用的消费者，声明本身不证明存在另一套相同实现或完整外部库语义。完整头文件覆盖只关闭这些本地定义、宏和声明的静态合同，不关闭dlopen库、aclTensor内部存储、队列或真机执行。

## 版本与模型优化验收

两版MLA预处理、Ring MLA、所选Utils模式helper和hash辅助的完整非注释token分别相同；此前所选Tensor转换至EXEC_ATB_CMD区域token相同；本次补齐整个AtbCommon.h，在消去C++反斜线续行这一格式差异后，完整非注释token仅主线GetApiFuncAddr末尾多return nullptr，全部注释同一。完整缓存键、序列化上限、Utils格式和Context合同见[执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)的补充；不由头文件完整阅读推导动态库或执行验证。

保存准确atb命名空间、模式、实际Q/Cache/LSE的shape/dtype/格式、CPU seqlen、前环状态、是否捕获与软件版本；将固定输出申请、连续化、Operation查询及每次workspace准备分开核对。先验证投影/位置编码约定、Cache状态、out别名与数值，再比较内存和性能。本次没有进行这些设备、并发或性能实验，不新增verified或耗时数字。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/MLAPreprocessAtb.cpp)（primary）：1–216。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/MLAPreprocessAtb.cpp)（implementation）：1–108。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/RingMlaAtb.cpp)（implementation）：1–168。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/RingMlaAtb.cpp)（implementation）：1–116。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：完整本地文件1–578。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/AtbCommon.h)（implementation）：完整本地文件1–523。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp)（implementation）：24–31。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.cpp)（implementation）：26–34。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：24–61,149–154。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：24–64,157–162。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：28–110。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCreate.h)（implementation）：28–120。
