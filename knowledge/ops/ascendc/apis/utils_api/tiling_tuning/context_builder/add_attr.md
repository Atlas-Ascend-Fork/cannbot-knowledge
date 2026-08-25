---
type: API
title: AddAttr
description: 设置算子的属性以及对应值
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/AddAttr.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# AddAttr

设置算子的属性名称及对应值。函数签名为 ContextBuilder& AddAttr(const std::string& attrName, attrValue)，通过重载支持 int64_t、bool、std::string、float 及对应 vector 类型。
参数 attrName 为算子属性名称，attrValue 为属性值，支持标量与向量两种形式。
返回当前 ContextBuilder 对象，支持链式调用。
约束：AddAttr 不支持重复添加同名的属性。
典型用法：builder.NodeIoNum(1,1).IrInstanceNum({1}).AddAttr("attr_1", 1).AddAttr("attr_2", true).AddAttr("attr_3", "stringValue")。

<!-- cannbot:related:start -->
## 相关

- [OpAttrDef](../../prototype_register_management/op_attr_def/op_attr_def.md)（`related`）：AddAttr 与《OpAttrDef》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddInputTd](add_input_td.md)（`same_topic`）：AddAttr 与《AddInputTd》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddPlatformInfo](add_platform_info.md)（`same_topic`）：AddAttr 与《AddPlatformInfo》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [BuildKernelRunContext](build_kernel_run_context.md)（`same_topic`）：AddAttr 与《BuildKernelRunContext》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：AddAttr 与《BuildTilingContext》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [CompileInfo](compile_info.md)（`same_topic`）：AddAttr 与《CompileInfo》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [ContextBuilder](context_builder.md)（`same_topic`）：AddAttr 与《ContextBuilder》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [ContextBuilder构造函数](context_builder_constructor.md)（`same_topic`）：AddAttr 与《ContextBuilder构造函数》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [SetOpNameType](set_op_name_type.md)（`same_topic`）：AddAttr 与《SetOpNameType》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
<!-- cannbot:related:end -->
