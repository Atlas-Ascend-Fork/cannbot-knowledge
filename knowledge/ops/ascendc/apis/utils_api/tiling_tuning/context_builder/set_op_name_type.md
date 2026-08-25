---
type: API
title: SetOpNameType
description: ContextBuilder &SetOpNameType(const std::string& opName, const std::string&
  opType)
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/SetOpNameType.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# SetOpNameType

设置算子的名字与类型。函数原型：ContextBuilder &SetOpNameType(const std::string& opName, const std::string& opType)。参数：opName（输入，算子名字）、opType（输入，算子类型）。返回值：当前ContextBuilder对象的引用，支持链式调用。无约束。在构造TilingContext时必须首先调用此方法设置算子名和类型，后续才能添加输入输出描述和属性。

<!-- cannbot:related:start -->
## 相关

- [AddInputTd](add_input_td.md)（`related`）：设置算子名和类型后才能添加输入 TensorDesc，二者有明确调用先后。
- [BuildTilingContext](build_tiling_context.md)（`related`）：完成名字、类型和 IO 元数据配置后，由 BuildTilingContext 生成 tiling 调用上下文。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《SetOpNameType》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：ContextBuilder构造函数 与《SetOpNameType》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [GetTilingFunc](../op_tiling_registry/get_tiling_func.md)（`same_topic`）：焦点处理OpTilingRegistry 加载动态库并取得 TilingFunc 的调测流程；SetOpNameType正文界定“ContextBuilder &SetOpNameType(const std::string& opName, const std::string& opType)”。候选承担 Registry 加载、对象构造、opName 设置、ContextBuilder 与 GetTilingFunc 调测，runbook复现函数依赖错误。
<!-- cannbot:related:end -->
