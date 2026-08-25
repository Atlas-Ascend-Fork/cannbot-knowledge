---
type: API
title: GetTilingFunc
description: 根据算子类型OpType获取对应的Tiling函数。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/OpTilingRegistry/GetTilingFunc.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# GetTilingFunc

根据算子类型 OpType 获取对应的 Tiling 函数。函数签名为 TilingFunc GetTilingFunc(const char* opType) const。
参数 opType 为算子类型字符串，需与原型定义时的算子类型保持一致。
返回值为 TilingFunc 函数指针（定义为 uint32_t(*)(gert::TilingContext*)），获取成功返回对应函数指针，失败返回空指针。
典型用法：先通过 OpTilingRegistry.LoadTilingLibrary 加载算子 so 库，再调用 GetTilingFunc("AddCustom") 获取 Tiling 函数并执行。
无特殊约束。

<!-- cannbot:related:start -->
## 相关

- [TilingFunc 未声明依赖读 axes 致 segfault](../../../../runbooks/compilation/tilingfunc_axes_segfault.md)（`exemplifies`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；TilingFunc 未声明依赖读 axes 致 segfault正文界定“vendor TilingFunc 内对 axes 输入(index 1) 调 GetInputTensor(1)->GetData<int32_t>() 而 未声明 TilingInputsDataDependency({1}) 时，C+”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [TilingDebug](../../../../guides/programming_guide/appendix/common_operations/tiling_debug.md)（`explains`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；TilingDebug正文界定“通过OpTilingRegistry加载编译后的Tiling动态库，使用ContextBuilder构建TilingContext并获取Tiling函数指针进行单独调测”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [ContextBuilder](../context_builder/context_builder.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；ContextBuilder正文界定“ContextBuilder上下文构建接口索引”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [LoadTilingLibrary](load_tiling_library.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；LoadTilingLibrary正文界定“根据输入路径加载Tiling动态库，支持算子包编译或动态库编译方式获取的so文件，返回加载是否成功”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [OpTilingRegistry](op_tiling_registry.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；OpTilingRegistry正文界定“OpTilingRegistry注册接口索引”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [SetOpNameType](../context_builder/set_op_name_type.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；SetOpNameType正文界定“ContextBuilder &SetOpNameType(const std::string& opName, const std::string& opType)”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
- [构造和析构函数](constructor_and_destructor.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；构造和析构函数正文界定“创建与释放OpTilingRegistry对象”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
<!-- cannbot:related:end -->
