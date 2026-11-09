---
type: Guide
title: vLLM Ascend 自定义 ACLNN 接入：构建、Torch 绑定与 Meta 契约
description: 沿 SOC 构建选项、cann_ops_custom、Torch dispatcher 和 Meta 实现接入新算子，验证图与部署产物，不将绑定完成当作完整内核正确性分析。 补充固定适配层的库搜索与缓存、Tensor描述符、workspace/stream和异常清理所有权。 补充Python Meta存在/overload门禁及原始launcher与扩展初始化宏的责任边界。
tags:
- task.implementation
- topic.model_adaptation
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/add_custom_aclnn_op.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/persistent_csrc_build_cache.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/add_custom_aclnn_op.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/aclnn_torch_adapter/op_api_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/aclnn_torch_adapter/NPUBridge.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/aclnn_torch_adapter/NPUBridge.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/aclnn_torch_adapter/NPUStorageImpl.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/aclnn_torch_adapter/NPUStorageImpl.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/recurrent_gated_delta_rule_v310/recurrent_gated_delta_rule_310_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/meta_registration.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/ops.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils.h
  role: implementation
created_at: '2026-10-29T09:54:45Z'
updated_at: '2026-11-03T05:09:40Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- register_meta_if_necessary
- REGISTER_EXTENSION
- TORCH_BIND_ASSERT
---

# vLLM Ascend 自定义 ACLNN 接入：构建、Torch 绑定与 Meta 契约

## 范围和交付边界

本卡是框架级ACLNN接入流程，覆盖按SOC构建和装载的核对，不声明新kernel在四类设备均支持。A2/A3/310P与950的runtime custom-op能力不同，先按[硬件profile](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)选实现族。完整Host/Device算子分析需专门producer，本卡不代替其tiling/内存与算法证明。

## 从构建到调用

在csrc下组织op_host/op_kernel，向build_aclnn.sh添加实际支持SOC与构建选项，多个CUSTOM_OPS以分号分隔；不能只添Python wrapper。设计说明记为vllm_ascend/cann_ops_custom；固定构建与运行源码实际使用vllm_ascend/_cann_ops_custom/vendors/custom_transformer，保留此路径差异。经torch_binding.cpp绑定torch.ops._C_ascend，运行初始化enable_custom_op后分别核对实际注册和动态库可见性。

torch_binding_meta.cpp提供图捕获所需Meta实现，必须与实际output shape/dtype及alias/mutation契约一致。Meta存在不证明设备kernel可运行，eager通过也不证明图捕获、动态shape或跨流语义正确。

## 增量缓存与迁移

若参与func.cmake的generated-kernel缓存，新增或改变generated/shared输入、recipe、工具链环境须同步cache identity参数。只改源码目录却遗漏间接header或SET_ENV可能误用旧artifact，不能把HIT当构建正确证据。缓存边界见[构建缓存指南](../bringup/vllm_ascend_incremental_build_cache.md)。

## 验收、停止与回退

对目标SOC核对包/库、dispatcher schema、Meta与device结果，覆盖dtype/shape/stride/空与尾块、原地和stream要求，再接模型与图。未知平台保持待确认，不据此判定支持或不支持；发现数值/shape/alias或缓存身份不完整时停用新分派，恢复已验证fallback并重建必要产物。本次只核对接入设计，没有编译或执行上游算子。


## 平台证据待补

自定义ACLNN设计仅要求按实际支持SOC构建，没有给新算子/整套接入链路的产品集合；hardware profile中的runtime custom-op能力也不能替代每个算子的支持证据。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。


## 中文接入说明与证据边界

add_custom_aclnn_op.po的9条业务译文对应当前英文接入说明，覆盖cann_ops_custom安装位置、torch.ops._C_ascend绑定、enable_custom_op、SOC构建项、分号分隔CUSTOM_OPS、Torch binding与Meta，以及generated/shared输入、配方和工具链的cache identity同步要求。源码目录/op_host/op_kernel、Python可调用和图Meta分别属于不同验收层，不能因为译文完整或一次dispatcher注册成功就跳过任一层。

缓存契约适用于参与func.cmake所述缓存构建的算子；它不宣称所有自定义算子都在该缓存内，也不提供全平台kernel能力。本卡仍保持draft/空平台，具体Host/Device算法、tiling/内存/同步和实际NPU验收继续由目标算子的分析与工程验证完成。本次没有构建、导入自定义算子或执行gettext/网站构建。

## 固定适配层与实际库路径

以下补充固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取op_api_common.h772行、NPUBridge/NPUStorageImpl四文件和V310 adapter53行，并有界核对utils、Torch binding/Meta及根CMake。只作数据阅读，未导入扩展、dlopen/dlsym、构建或执行上游；共享适配器存在不构成任意算子的硬件支持证据，继续draft/空平台。

设计文档写vllm_ascend/cann_ops_custom；固定源码实际用vllm_ascend/_cann_ops_custom/vendors/custom_transformer。bootstrap_custom_op_env以utils所在包目录为根，在vendor目录存在时将路径补入ASCEND_CUSTOM_OPP_PATH；include_vendor_lib=True时才额外补入其op_api/lib到LD_LIBRARY_PATH。_prepend_env_path仅在尚无该项时插入首位，已有项不重新排序。根CMake的ORIGIN rpath也指向带下划线的目录。接线以实际构建/安装和库位置核对，保留文档及对应译文的路径差异，不把两个目录当成已证明相同。

根CMake显式要求PyTorch2.10.0，并把aclnn_torch_adapter下cpp编入扩展；它沿所选CANN和torch_npu头文件构建。NPUStorageImpl布局、ScalarType枚举和函数指针转换仍是具体版本ABI边界；本次没有验证实际安装的wheel/动态库匹配。

## enable_custom_op 是注册状态，不能代替执行验收

enable_custom_op缓存_CUSTOM_OP_ENABLED。VLLM_BATCH_INVARIANT为真或硬件profile缺RUNTIME_CUSTOM_OPS时缓存False并返回；不能仅据注释里的芯片名称决定实际分支。普通非compiling路径先bootstrap，再import扩展、再import meta_registration。

第一次ImportError若包含libcust_opapi.so且不在编译中，才bootstrap(include_vendor_lib=True)并重试；重试失败或其他ImportError缓存False、打印warning。捕获范围是ImportError，不是所有异常。编译中跳过bootstrap不等于环境已准备；True只表示这次注册流程成功，不证明具体符号、算子数值、state副作用或graph replay通过。

## ACLNN符号装载顺序与缓存

GetOpApiFuncAddr逐符号按下列顺序寻找：

1. 全局g_custom_lib_path：由扩展初始化时的ASCEND_CUSTOM_OPP_PATH按冒号分隔，每项追加op_api/lib，逐库找libcust_opapi.so。
2. 全局g_default_custom_lib_path：从ASCEND_OPP_PATH/vendors/config.ini的load_priority逗号列表构造vendor库目录。
3. 静态libopapi_transformer.so handle。
4. 静态libopapi.so handle。

GetOpApiLibHandler使用dlopen(RTLD_LAZY)，GetOpApiFuncAddrInLib使用dlsym；源码未在这些分支中提供逐handle的dlclose。CANN9.2拆分transformer库的注释解释搜索顺序，不能据此保证任意9.1基础环境或9.2组件的二进制兼容。

路径列表在全局初始化时读取环境。EXEC_NPU_CMD的执行函数、GetWorkspaceSize函数和HugeMem辅助函数地址分别以static保存，转换/销毁函数也缓存各自地址。进程中较晚改环境或安装库不能假定重试就会刷新全部地址；首次解析为nullptr的static变量也不会因后来文件出现自动重算。两个阶段的符号分别搜索，不能只凭函数名配对就断言来自同一DSO。

验收时记录真实库路径、符号归属、扩展import与环境准备顺序，再决定重建匹配产物或重启干净进程。函数找不到不先归为kernel计算故障，也不通过任意库抢占去掩盖版本不匹配。

## Tensor描述符：view、storage与NPU格式分开

ConvertType(at::Tensor)对undefined返回nullptr；缺aclCreateTensor地址也返回nullptr。dtype通过kATenScalarTypeToAclDataTypeTable映射，ACL_DT_UNDEFINED或itemsize0触发TORCH_CHECK；映射表含低精度枚举不证明任意具体算子支持这些dtype。

普通base format路径按rank3/4/5分别选择NCL/NCHW/NCDHW，其余为ND，storageDims由storage.nbytes/itemsize计算为一维物理容量。传aclCreateTensor的是逻辑sizes、strides、storage_offset和storage起始地址，而不是把data_ptr、逻辑numel和storage容量混成一个量。

非base的PrivateUse1 Tensor通过NPUBridge取得NPUStorageImpl的npu_format_与storage_sizes_；NPUBridge使用static_cast读取自定义StorageImpl布局，不在此做动态类型验证。NPUStorageDesc还有base sizes/strides/offset、origin format和dtype信息，但不能把其存在当作本函数逐项验证了所有字段或外部torch_npu布局。

stride/offset被编码进描述符不表示下游每个kernel都支持任意view。state原地更新、实际storage extent、物理padding、NPU format和输出回写均须按具体算子核对；不能把descriptor成功创建等同于非连续输入数值通过。

## Scalar、optional与列表转换边界

ConvertType对可选Tensor仅在has_value且defined时转换，否则传null；可选数组/Scalar按has_value处理。TensorList先把每个Tensor转成aclTensor指针，再建立aclTensorList；失败和子项销毁归属不能仅由列表句柄存在推断。

ConvertTensorToScalar直接按dtype解引用tensor.data_ptr，属于wrapped number处理链；CopyScalarToDevice先构造CPU Tensor，再pin_memory并以non_blocking方式复制到PrivateUse1的device index0。这里硬编码的0不等于调用者当前NPU，临时aclInput在函数返回后依赖外部描述符/分配器的存活语义，本函数只返回aclTensor指针。需要按实际torch_npu分配器和执行语义验证跨device、异步及临时量生命周期；本次未复现错误。

ConvertType(at::Scalar)只对该重载列出的Double、Long、Bool和ComplexDouble创建aclScalar，其他分支返回null；通用ScalarType映射不替代该重载的支持范围。基本标量参数还可能经模板原样传递，应按调用点的真实C++类型核对，不能统一当作Tensor转换。

## EXEC_NPU_CMD 的两阶段调用与workspace所有权

宏先解析并检查执行/查询符号，再读取当前NPU stream，初始化workspace_size=0与executor=nullptr，条件调用InitHugeMemThreadLocal。ConvertTypes把调用参数及workspace/executor输出指针转成tuple，ConvertToOpApiFunc按转换后的C++类型reinterpret_cast函数指针，调用GetWorkspaceSize并检查返回0。

这一路没有包含每个公开ACLNN头来提供同样的编译期原型检查。参数次序、可选值、标量位宽和输出指针必须逐调用点核对。头中g_hashBuf、AddParamToBuf和CalcHashId的声明不代表本宏缓存了executor或workspace；本宏每次都发起workspace查询。

workspace_size非0时，宏在if块内分配kByte workspace_tensor，仅把storage.data转为workspace_addr。该Tensor局部变量离开if块后，回调捕获的是raw pointer、size、executor、stream和转换后的tuple，没有显式捕获workspace Tensor，本宏也没有recordStream所有权登记。

这是一条必须进一步验证的静态所有权边界。实际是否安全取决于OpCommand::Run/custom handler、分配器和stream语义；这些外部实现未在固定源码集合闭合，不能直接宣布已经UAF，也不能仅因at::empty成功或两阶段返回0宣布异步生命周期安全。验收应明确workspace的持有者、释放点、命令提交/完成时间和stream，而非只保留裸地址。

## 正常清理与异常清理分开核对

OpCommand设置Name和CustomHandler后Run。正常回调先调用execute并检查返回0，再ReleaseConvertTypes销毁转换句柄，条件ReleaseHugeMem；cmd.Run返回后条件UnInitHugeMemThreadLocal。Release对Tensor、Scalar、IntArray、BoolArray、TensorList分别解析对应Destroy符号，缺符号则直接返回；其他模板参数Release为空操作。

GetWorkspaceSize或execute非0会TORCH_CHECK抛出，后续的显式Release/ReleaseHugeMem/UnInit路径可能未走到。该宏没有覆盖这些资源的显式RAII清理guard。这里没有测量内存泄漏或假设CANN内部资源全部归该宏；应分别验证转换句柄、executor、HugeMem和workspace的真实所有者与失败路径。

TensorList内部子句柄是否由aclDestroyTensorList统一释放、外部executor如何销毁、Destroy是否允许null，以及异步device任务消费描述符的时间，都不能由本头声明补齐。错误排查保留第一阶段/第二阶段返回、实际函数/库、参数、资源状态和stream完成证据，避免重复释放或仅重试隐藏原始故障。

## 用V310接线核对三层合同

53行npu_recurrent_gated_delta_rule_310 adapter按value.sizes/options分配output，把double scale_value显式转float，按query/key/value/beta/state/lengths/indices/g/gk/accepted/scale/output顺序调用EXEC_NPU_CMD。它传mutable state引用，但不在此补全dtype、slot或padding校验。

固定310P Torch schema中的state为普通Tensor；C++ mutable参数及CANN的stateRef原地更新表达了副作用意图。对应Meta只按value.sym_sizes/options返回empty_symint，不推进state。schema、Meta、真实调用者和CANN内核各自是独立合同，不能由Meta存在推出alias/mutation或图回放正确。

完整CANN入口、Host/POD、UB与Device实现沿[RecurrentGatedDeltaRuleV310算子卡](../../operators/aclnn/transformer/attention/vllm_ascend_recurrent_gated_delta_rule_v310_310p.md)；验收层次沿[310P GDN数值指南](../bringup/vllm_ascend_310p_gdn_numerical_validation.md)。本节没有改变Torch schema、修复上游或运行图测试，也不提供跨版本强制改法。

## 新算子接入交付补充

交付时将库/版本/符号、Torch schema与dispatch key、Meta shape/dtype/state、descriptor view/storage/format、标量宽度、workspace与转换句柄/异常清理、stream提交与完成逐项记录。先在获准目标栈验证普通连续输入，再覆盖真实非连续view、optional、状态、临时量、零workspace与异常路径；实际算子支持范围和图能力分别验收。

仅完成加载、descriptor创建、控制返回或源码核对时，明确标记对应层次。没有实际运行就不声称通过NPU、graph、多stream、精度、吞吐或Agent A/B；未知硬件范围继续保留，不由共享宏推广为全平台支持。


## Python Meta兜底与C++扩展壳的实际责任

新增全文核对同提交 meta_registration.py、csrc/ops.h、csrc/utils.h。Python模块创建 _C_ascend 的 IMPL Library，先查 Meta dispatch 注册列表，已存在则返回；扩展未编译相应operator时按torch.ops属性跳过，再执行lib.impl。overload参与完整schema名字，而存在检查只看基础op；它不是对每个overload都做完整ABI验证。模块实际只在BGMV_SGMV_META_REGISTRATION能力门禁下给bgmv_expand/sgmv_expand注册返回empty_like(y)的Meta，没有提供所有算子的自动Meta生成。

这些Python Meta只给输出shape/dtype，不访问weight/index值、写实际y或证明mutation/alias约定。能力位、基础符号存在、Meta注册和真实图lowering分别核对；“跳过重复注册”不代表动态替换了旧实现。

ops.h四个BGMV/SGMV launcher声明使用裸stream/Tensor指针、AscendType及uint32维度/indices长度，expand另区分y和y_out、slice_offset与full output宽度。声明无边界/容量检查，调用方的int64 shape转uint32、buffer寿命和切片范围不能从头文件推出安全。utils.h的REGISTER_EXTENSION仅构造Python module，Torch library宏展开处理namespace宏；模块可import不表示每个dispatcher schema或device kernel已注册。TORCH_BIND_ASSERT抛带文件/行的TrochBindException，它不提供资源RAII回滚。
