---
type: Guide
title: FXRT aclnn算子执行器：哈希缓存、可重复执行器与注册边界
description: 记录FXRT Ascend算子经AclnnExecutor两段式下发opapi的机制、按元数据哈希的执行器LRU缓存、地址重绑定，以及FXRT_REG_OP注册表与CheckOpSupport白名单的回退边界。
tags:
- task.implementation
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_executor.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_cache.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_hash.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_hash.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/hash_buf.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/hash_buf.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_converter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_converter.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_common_meta.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_common_meta.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_deleter.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/opapi_lib_loader.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/opapi_lib_loader.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/opapi_utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/opapi_utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_register.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_register.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/custom_op_register.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/custom_op_register.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/operator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/operator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/kernel_lib.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/kernel_lib.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_def/ops.list
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_def/ops_name.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_def/ops_name.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/op_support.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/op_support.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/op_constants.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/aten_convert.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/async.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_custom_operator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_custom_view_operator.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_custom_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_custom_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/mul.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/include/custom_op_api.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ops/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ops/load.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/_logging.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/collective.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/ascend/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_api.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_collective.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/dynamic_lib_loader.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/dynamic_lib_loader.cpp
  role: implementation
created_at: '2026-11-13T04:14:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT aclnn算子执行器：哈希缓存、可重复执行器与注册边界

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的FXRT Ascend aclnn算子层：AclnnExecutor两段式下发、按参数哈希的执行器缓存、opapi动态加载、FXRT_REG_OP/CustomOpRegistry注册表、CheckOpSupport白名单，以及Python侧自定义算子编译加载。本文只做静态阅读，未导入、构建或运行FXRT；产品配套矩阵未知，整卡draft、platforms为空。执行模式、捕获与输出复制见[FXRT推理运行时](torch_npu_fxrt_runtime.md)，前端Schema匹配见[FXRT前端降级](torch_npu_fxrt_frontend_lowering.md)，本卡不重复。

## 两段式下发与动态库加载

每个aclnn算子类持有一个`AclnnExecutor(opApiName)`：构造时经opapi动态库加载器解析`<opApiName>`与`<opApiName>GetWorkspaceSize`两个符号，任一缺失直接抛异常，不静默回退。CalcWorkspace阶段调用GetWorkspaceSize取得workspace大小，Launch阶段用同一执行器提交。opapi符号经`GET_ACLNN_OP_FUNC`从libopapi按需取得；`aclSetTensorAddr`、`aclSetDynamicTensorAddr`、`aclSetAclOpExecutorRepeatable`等公共元接口经`GET_ACLNN_COMMON_META_FUNC`解析，解析失败按“不支持该能力”处理而不是崩溃。

## 哈希键只含元数据，不含数据指针

`CalcAclnnHash(opApiName, args...)`把算子名和全部实参序列进thread-local缓冲再混合成64位哈希。对Tensor实参，`GatherHash`只写入：view shape、storage shape、dtype（1字节）、strides、storageOffset；**不写入data_ptr，也不写入数据内容**。标量、字符串、IntList、Tuple按值写入；`std::pair<vector<int64_t>,bool>`里fias这类“IntList按Tensor处理”的参数会额外推进tensorIndex。这意味着两个地址不同但元数据完全一致的Tensor命中同一缓存键——这是执行器可跨次复用的前提，也是它的边界：键碰撞或元数据未覆盖的差异（例如同一storage内不同别名布局组合）不会被该缓存区分，须靠上层ShapeKey与重绑定校验兜底。

## 可重复执行器缓存与地址重绑定

GetWorkspaceSize先查`CacheEntryManager`：命中则直接返回缓存workspace大小。未命中时生成`aclOpExecutor`，并调用`aclSetAclOpExecutorRepeatable`询问该执行器是否可重复；只有可重复的执行器连同转换后的参数一起进入LRU缓存（容量来自`GetAclnnCacheCapacity()`，容量0或hashId为0时完全禁用缓存；超出容量淘汰链表尾部）。不可重复的执行器不缓存，Launch后由第二段接口自动释放，参数释放走注册的`releaseParamsFunc_`。

缓存命中路径在Launch前用`CallUpdateAddr`把当前实参的Tensor地址重绑定到缓存执行器：`aclSetTensorAddr`按tensorIndex更新单Tensor，`aclTensorList`经`aclSetDynamicTensorAddr`按irIndex+relativeIndex更新；`UpdateAddr`按参数类型逐个推进ir/tensor下标。地址更新失败抛异常，不降级为重新建执行器。因此“缓存命中”省的是参数转换与GetWorkspaceSize调用，不省Launch本身；若某算子的aclnn实现内部缓存了与地址相关的状态，该机制无法感知，需按算子单独验证。

## 注册表与CheckOpSupport白名单

`FXRT_REG_OP(op, Class, Ascend)`把算子名注册进设备工厂；首次取工厂时按`libops_ascend`/`libops_cpu`（torch前端启用时再加`libops_torch`）前缀加载算子插件库，加载失败抛异常。重复注册同名算子直接异常。`FXRT_REG_OP_PROTOTYPE(op, n)`登记该算子固定Tensor输入数，注册点即原型唯一事实源。

`CheckOpSupport`决定前端`check_op_support`的非零返回与custom_call回退：设备从输出/首个Tensor输入推导；未在目标设备注册的算子返回UnsupportedDevice。**白名单算子（make_tuple、tuple_getitem、return、gather、constant_pad_nd、full_like、clone、contiguous、embedding，以及view/reshape/unsqueeze/squeeze/flatten/alias、permute_view/permute、slice_view/slice/narrow_view/narrow、getitem_slice、gather_v2、index_tensor、as_strided_view、empty_strided等）在非CPU设备直接放行**——它们走FxConverter Path C/ViewAlias/恒等旁路而非aclnn stub；CPU没有Path C，白名单算子若无CPU注册仍降级custom_call。原型登记过的“全Tensor定长”算子还要求：过滤掉None控制边后，实际输入全部是Tensor且数量与原型一致，否则返回UnsupportedInputType。控制边None（如End输出）不是数据输入，不计入。

## 薄包装同族：一张表读到底

ascend/aclnn下约95个单API算子文件（add、mul、sub、div、eq/gt/le/ne/ge及scalar变体、exp、neg、rsqrt、sigmoid、silu、relu、leaky_relu、swiglu、bitwise_*、pow_*、remainder_*、amax、reduce_sum/mean、cast、where、tril、softmax、topk、embedding、cat、stack、repeat、arange、slice、split_tensor、split_with_size、permute、squeeze/unsqueeze/flatten/narrow/chunk/select/unbind的非view形式、inplace_add/fill/index_copy系列、scatter_nd_update等）是同一模式的实例化：构造绑定`AclnnExecutor("aclnnXxx")`，CalcWorkspace/Launch把Tensor与标量按固定下标转发给GetWorkspaceSize/Launch，尾部`FXRT_REG_OP`注册。op名到aclnn API名的映射经机械提取并与抽样阅读一致；除转发外没有独立shape/dtype/回退逻辑。本卡不逐文件复述该表；查映射时以固定提交的实际文件为准，不要从op名推断API名（例如getitem_slice绑定的是aclnnSliceV2相关接口、iota绑定的是aclnnArange，均非按op名拼接）。带独立前置约束或多元数据/多API选择的算子另见[FXRT量化/MoE/融合特例算子](torch_npu_fxrt_quant_moe_fused_specialized_ops.md)与[FXRT view零拷贝与元数据算子](torch_npu_fxrt_view_zero_copy_and_metadata_ops.md)。

## 自定义算子注册与Python编译加载

`CustomOpRegistry`是独立于ops.list的运行时注册表：`REGISTER_CUSTOM_OP(name, Class)`跨CPU/NPU动态注册，`CreateCustomOperator`按短名创建。`AclnnCustomOperator`/`AclnnCustomViewOperator`是对外提供的基类合同：自定义view算子须在CalcWorkspace里自行用`UpdateTensorViewInfo`计算输出元数据（通用ref元数据同步会跳过shape改变的输出）、声明输出-输入ref对并在结尾`CheckStorageMatch`验证别名真的成立；Launch返回SUCCESS且`NeedLaunch()`为false。Python侧`fxrt.ops.load`负责把用户C++源码编译成.so再dlopen：构建目录默认`$PWD/.fxrt_custom_cache/<name>`，`build.lock` O_EXCL文件锁串行化编译，库按编译哈希缓存，已加载库直接复用。`fxrt.collective`与`pybind_collective`把CollectiveManager经`fxrt._fxrt_collective`暴露给Python；`config/ascend/__init__`实例化OpPrecisionConf/AclGraphConf单例。这些入口存在不表示任意自定义算子已通过数值或别名验证。

## 边界与验证方式

本卡全部结论来自固定提交的静态阅读：执行器缓存、地址重绑定、白名单回退均未在设备上复现。采用前应固定TorchNPU/CANN组合，分别在大/小`GetAclnnCacheCapacity()`与0容量下比较命中日志（RT_VLOG VL_OPS的miss/cache行）、首次与稳态耗时；对含IntList-as-Tensor、Tuple、可选Tensor的算子逐项核对地址重绑定下标；白名单算子确认实际落到Path C/ViewAlias而非误判支持。本卡不把这些机制写成性能收益承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_executor.h)（primary）：定向范围1–137。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_cache.h)（implementation）：定向范围1–406。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/aclnn_hash.cpp)（implementation）：定向范围1–44。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/utils/hash_buf.cpp)（implementation）：定向范围1–70。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/op_support.cpp)（implementation）：定向范围1–199。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_register.h)（implementation）：定向范围1–205。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/custom_op_register.h)（implementation）：定向范围1–104。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/aclnn_custom_view_operator.h)（implementation）：定向范围1–134。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ops/load.py)（implementation）：定向范围1–80。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_def/ops.list)（implementation）：全表159行枚举。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/aclnn/mul.cpp)（implementation）：同族薄包装抽样。
