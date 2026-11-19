---
type: Guide
title: ATB依赖入口：公共SDK声明、占位库与Python装载
description: 闭合公共张量/图/Context/Operation声明与构建占位库，核对Python顶层装载、延迟补丁、错误保留和两版曝光API差异。
tags:
- task.implementation
- topic.compilation
- topic.architecture
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/types.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/atb_infer.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/context.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/operation.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/libs/atb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/libs/build_stub.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/types.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/atb_infer.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/context.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/operation.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/libs/atb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/libs/build_stub.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh
  role: implementation
created_at: '2026-11-11T05:22:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ATB依赖入口：公共SDK声明、占位库与Python装载

本卡限定OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布dedc316708372c9a8bfde4527abd2a94b74840f5中所列公共SDK头、占位库、Python装载器及构建选段。18个完整文件来自两版各9个文件，其他构建文件仅审准确选段；没有导入模块、运行脚本、加载动态库或设备验证，保持draft/空平台。已有[LibTorch部署入口](../../bringup/torch_npu/torch_npu_libtorch_build_and_deployment.md)说明导出库和C++目录，本卡补实际公共声明与装载控制流，不扩其硬件表到所有ATB功能。

## 张量与图结构：声明边界不是自动校验

atb_infer.h只按顺序汇集context、operation、svector、types、utils和infer_op_params六个头，不在自身实现Kernel。以下公共结构位于types.h；SVector内部实现和其余infer_op_params定义不因被include而整文件闭合。

| 声明 | 精确本地字段/默认值与文档约束 |
| --- | --- |
| Status / MAX_DIM | Status=int32_t；MAX_DIM为uint32_t的8。 |
| Dims | int64_t dims[8]，数组本身无逐项默认初始化；uint64_t dimNum默认0。注释要求每维>0、维数(0,8]，默认0不等于已经满足该要求。 |
| TensorDesc | dtype=ACL_DT_UNDEFINED、format=ACL_FORMAT_UNDEFINED、shape为Dims。其警告说Atlas推理系列不支持ACL_BF16，不把桥接可表示BF16当成产品支持。 |
| Tensor | desc及deviceData=nullptr、hostData=nullptr、uint64 dataSize=0；dataSize描述相应地址内容大小，不自动分配Storage。 |
| VariantPack | inTensors/outTensors均为SVector<Tensor>，分别保存输入和最终输出。 |
| Chunk | uint32 chunkNum=1、chunkIndex=0，用于Host侧split描述。 |
| ReshapeFunc / InferShapeFunc | 前者void(const Dims&,Dims&)，后者Status(const SVector<TensorDesc>&,SVector<TensorDesc>&)。声明不会自行执行推导。 |
| Node | Operation*=nullptr；inTensorIds/outTensorIds、逐输入inTensorReshapeFuncs及inTensorChunks。文档明确要求inTensorIds、outTensorIds、inTensorReshapeFuncs这三列表的元素顺序对应Tensor顺序；inTensorChunks在此仅记录字段存在，不扩大该顺序合同。 |
| GraphParam | name字符串；inTensorNum/outTensorNum/internalTensorNum均uint32默认0；nodes为std::vector<Node>，inferShapeFunc=nullptr。文档要求名字仅字母/数字/下划线且≤128，每类Tensor数≤256、节点数<1024、节点按依赖执行顺序排列，Tensor ID落在[0,三类数量之和-1]。这些是注释合同，本结构没有相应检查函数。 |

ErrorType以int为底层类型，从NO_ERROR=0顺序递增到27；完整分类如下，不能把任何非零状态或空指针当成已验证成功：

| 值 | 枚举名 |
| --- | --- |
| 0–4 | NO_ERROR、ERROR_INVALID_PARAM、ERROR_INVALID_GRAPH、ERROR_INTERNAL_ERROR、ERROR_RT_FAIL |
| 5–9 | ERROR_INVALID_IN_TENSOR_NUM、ERROR_INVALID_TENSOR_DTYPE、ERROR_INVALID_TENSOR_FORMAT、ERROR_INVALID_TENSOR_DIM、ERROR_INVALID_TENSOR_SIZE |
| 10–14 | ERROR_OPERATION_NULL_RUNNER、ERROR_GRAPH_INFERSHAPE_FUNC_FAIL、ERROR_CANN_ERROR、ERROR_INVALID_TENSOR_INI_MATCH、ERROR_INVALID_TENSOR_ADDR |
| 15–19 | ERROR_INVALID_TENSOR_NUM、ERROR_INVALID_TENSOR_DIM_NUM、ERROR_INVALID_SINGLE_OPERATION_PARAM、ERROR_GRAPH_NODE_RESHAPE_FUNC_FAIL、ERROR_INVALID_GRAPH_NODE_CHUNK |
| 20–24 | ERROR_INVALID_CONTEXT_ADDR、ERROR_INVALID_STREAM、ERROR_INVALID_WORKSPACE_SIZE、ERROR_INVALID_WORKSPACE_ADDR、ERROR_INVALID_OPERATION_ADDR |
| 25–27 | ERROR_HCCL_FAIL、ERROR_OUT_OF_DEVICE_MEMORY、ERROR_OUT_OF_HOST_MEMORY |

## Context、Operation和Utils都是公共接口层

Context是带默认构造/虚析构的抽象类。SetExecuteStream(aclrtStream)返回Status，GetExecuteStream() const返回流；SetAsyncTilingCopyStatus(bool)返回Status，GetAsyncTilingCopyStatus() const返回bool。注释将Context用于运行/tiling资源，并说异步tiling复制可创建流和event；头中方法为纯虚，未给实际资源实现。CreateContext(Context**)和DestroyContext(Context*)只有Status声明。

Operation同样为默认构造/虚析构的抽象类：GetName() const返回string，InferShape在const方法中从输入描述引用写输出描述引用，GetInputNum/GetOutputNum返回uint32；Setup(const VariantPack&,uint64_t& workspaceSize,Context*)返回Status，Execute(const VariantPack&,uint8_t* workspace,uint64_t workspaceSize,Context*)返回Status。这里明确区分所需字节输出引用与执行时地址/容量，不用空声明代替[执行准备指南](../../torch_npu_atb_paged_attention_execution_lifecycle.md)中的实际Setup/Execute消费者。

公共CreateOperation模板接const参数及Operation**，DestroyOperation接Operation*；注释要求Create之后适当Destroy以免泄漏。CloneOperationParam(const Operation*,Param&)注释承诺参数浅拷贝，UpdateOperationParam(Operation*,const Param&)声明更新；这些声明没有在此给出缓存失效、线程安全或原地更新的执行实现。

Utils只声明GetAtbVersion()->string、GetTensorSize(Tensor/TensorDesc)->uint64和GetTensorNumel(Tensor/TensorDesc)->uint64两组重载；因此不能在这几个头里把实际存储字节计算简化为逻辑numel。QuantParamConvert(const float*,uint64_t*,count)的注释是把float的位放到uint64低32位、高32位置0，不是浮点数值直接转整数的同一算法；本头没有对应函数体。

## 构建占位库不能充当NNAL运行实现

libs/atb.cpp自己说明用于编译libatb.so的staking函数；它定义CreateContext、DestroyContext、CreateOperation模板及DestroyOperation，四者都直接return0。CreateContext不写入Context**，CreateOperation也不写入Operation**，没有真实Context/Operation构造或算子执行。模板定义未附显式实例化，不能仅凭源码名字认证实际导出的每个符号。这里的0不能作为“对象已创建、ATB可运行”的验收信号。

build_stub.sh取自身目录、cd到该目录，再以gcc -fPIC -shared -o libatb.so及相邻inc/ACL头路径编译atb.cpp。所选gencode末行调用该脚本；所选CMake ATB目标对ops/atb和公共utils的CPP作glob、构建op_plugin_atb共享目标，设置-Bsymbolic-functions，并链接torch_npu与这个仓内libatb.so路径。相同文件名不等于真实NNAL包，源码构建/链接成功也没有证明部署时装载的是所需运行库。仅静态阅读这些脚本文本，未执行、生成或替换任何库。

## Python模块先尝试装库，延迟的是绑定/报错

_atb_ops.py先创建ModuleType('atb')，直接写torch_npu.atb和sys.modules['torch_npu.atb']，没有先检查已有同名模块。随后模块顶层try按__file__.parents[2]/lib/libop_plugin_atb.so构造路径，调用外部PathManager检查、torch.ops.load_library，并导入ATB Meta注册。因此“lazy”并不表示第一次调用前没有装库尝试，模块存在也不等于装库成功。

只捕获OSError，保留原异常GLOBAL_E，并构造同errno、复制traceback的NNAL_EX。消息含libatb.so时给NNAL安装/set_env线索，含undefined symbol时改为NNAL与torch_npu版本匹配线索；两个独立if使后者可覆盖前者。其他OSError的提示字符串可为空，其他异常类型不在这个except处理。源码没有在后续每次调用重新执行顶层装库try。

API_LIST绑定到torch_npu根，ATB_API_LIST绑定到ATB_MODULE；两版共有的根列表是_matmul_add_fp32、_quant_rms_norm、_group_topk、_paged_attention、_paged_attention_mla、_paged_attention_quant、_quantize_per_tensor、_reshape_and_cache、_reshape_and_cache_siso、_rotary_embedding、_flash_attention、_flash_attention_unpad、_paged_attention_splitfuse、_flash_attention_qlens、_paged_attention_get_workspace（这些名称均带_npu前缀）。主线额外有_npu_flash_attention_v3、_npu_flash_attention_unpad_v2、_npu_paged_attention_splitfuse_v2，根列表18项；发布为15项。

两版ATB_API_LIST相同11项：npu_paged_cache_load、npu_multi_head_latent_attention、_npu_multi_head_latent_attention_get_workspace、_npu_paged_attention_v2、_npu_paged_attention_v2_get_workspace、_npu_flash_attention_v2、_npu_flash_attention_prefix_v2、npu_fused_add_topk_div、npu_ring_mla、npu_self_attention_prefix_encoder、npu_mla_preprocess。列表是曝光入口，具体重载/schema/产品条件另核，不能把列表数量当已实现或验证模型优化数量。

generate_atb_lazy_function遍历两列表，在本模块globals创建同名generated_function。每个函数保留名字，经wraps装饰的wrapper先调用_register_atb_extensions，再getattr(torch.ops.atb,api_name)转发原args/kwargs。_register_atb_extensions带无界lru_cache：先在NNAL_EX非空时从GLOBAL_E抛出，随后_patch_atb_ops直接用真实torch.ops.atb对象覆盖两个命名空间；最后仅在非torch.compiler.is_compiling时追加文档。本函数没有重新装库或清空早先错误状态的分支。

_patch_atb_and_loadso本身只是把globals里的lazy函数装到torch_npu或ATB_MODULE，名字不能解释为它又load_library。op_plugin/python/__init__.py实际导入文档函数、这个patch函数及普通_fake_registrations，先调用patch、再无条件调用文档追加；因此包初始化文档与首次lazy注册的条件文档追加是两个不同调用点。文档可见或函数可见不能证明底层符号和设备执行已经有效。

## 两版对照与未闭合依赖

公共五头、占位CPP完整phase2非注释token相同；注释差异仅operation/types许可头及两处注释换行归并，其余公共说明同一。build_stub文本相同、Python包init完整AST相同；_atb_ops的完整AST差仅主线三项根API，其他差异为空白。固定CMake ATB目标和gencode调用选段同语义，不能据此把两个完整构建系统也判定相同。

完整infer_op_params.h其余参数、SVector存储实现、真实NNAL库/ACL、torch.ops加载和Meta函数体均不在本卡范围。PA/FA/MLA/量化等指南所绑定参数头选段继续保留；不因本卡包含公共头而宣称整个vendor、ATB或OpPlugin仓库已全量完成。定位导入/缺符号时保留准确提交、部署库路径、原始异常及对应schema，再核实际运行环境；本卡不新增verified、硬件支持或性能结果。

## 固定证据

以下证据逐项绑定原始字节SHA及真实范围，完整文件与选段分开列出。

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/types.h)（primary）：1–193。
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/atb_infer.h)（implementation）：1–22。
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/context.h)（implementation）：1–106。
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/operation.h)（implementation）：1–151。
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/utils.h)（implementation）：1–89。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/libs/atb.cpp)（implementation）：1–22。
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/libs/build_stub.sh)（implementation）：1–5。
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：1–132。
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/__init__.py)（implementation）：1–8。
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt)（implementation）：44–57。
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh)（implementation）：79–79。
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/types.h)（implementation）：1–195。
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/atb_infer.h)（implementation）：1–22。
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/context.h)（implementation）：1–106。
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/operation.h)（implementation）：1–147。
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/utils.h)（implementation）：1–89。
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/libs/atb.cpp)（implementation）：1–25。
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/libs/build_stub.sh)（implementation）：1–5。
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：1–131。
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/__init__.py)（implementation）：1–8。
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/CMakeLists.txt)（implementation）：34–47。
- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh)（implementation）：73–73。
