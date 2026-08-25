---
type: API
title: ContextBuilder构造函数
description: 创建ContextBuilder对象时，初始化数据成员。
tags: [task.lookup, topic.implementation.api_layer.utils_api]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/Tiling_tuning/ContextBuilder/ContextBuilder_constructor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# ContextBuilder构造函数

创建ContextBuilder对象时初始化数据成员。函数原型：ContextBuilder()。无参数、无返回值、无约束。ContextBuilder类用于手动构造TilingContext或KernelContext对象，支持Tiling函数和TilingParse函数的独立验证。构造后通过链式调用SetOpNameType、NodeIoNum、AddInputTd、AddOutputTd、AddAttr等方法配置上下文，最后调用BuildTilingContext或BuildKernelRunContext生成目标上下文。

<!-- cannbot:related:start -->
## 相关

- [561002：TilingParse 未生效，CompileInfo 为空](../../../../runbooks/compilation/561002_tilingparse_compileinfo.md)（`exemplifies`）：ContextBuilder构造函数 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [AddPlatformInfo](add_platform_info.md)（`related`）：ContextBuilder构造函数 与《AddPlatformInfo》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Inputs（Utils API）](inputs.md)（`related`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《ContextBuilder构造函数》说明创建ContextBuilder对象时，初始化数据成员。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [IrInstanceNum](ir_instance_num.md)（`related`）：ContextBuilder构造函数 与《IrInstanceNum》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [KernelRunContextHolder结构定义](kernel_run_context_holder_struct_definition.md)（`related`）：《KernelRunContextHolder结构定义》说明该结构体为ContextBuilder类最终的构造结果，可通过指定的接口获取内部算子信息或获取KernelContext类的对象。；《ContextBuilder构造函数》说明创建ContextBuilder对象时，初始化数据成员。。二者在KernelRunContextHolder是ContextBuilder最终产物，BuildKernelRunContext、BuildTilingContext和Inputs/Outputs决定其内容上存在可执行的直接衔接。
- [NodeIoNum](node_io_num.md)（`related`）：ContextBuilder构造函数 与《NodeIoNum》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Outputs（Utils API）](outputs.md)（`related`）：ContextBuilder构造函数 与《Outputs（Utils API）》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [Tiling调测](../tiling_tuning.md)（`related`）：ContextBuilder构造函数 与《Tiling调测》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [AddAttr](add_attr.md)（`same_topic`）：AddAttr 与《ContextBuilder构造函数》的实质衔接是：AddAttr 是 ContextBuilder 链式构造 tiling/kernel 上下文的一环；构造、I/O、算子名、平台、CompileInfo 和 Build 方法共同决定属性如何进入 KernelRunContext。
- [AddInputTd](add_input_td.md)（`same_topic`）：ContextBuilder构造函数 与《AddInputTd》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [AddOutputTd](add_output_td.md)（`same_topic`）：ContextBuilder构造函数 与《AddOutputTd》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [BuildKernelRunContext](build_kernel_run_context.md)（`same_topic`）：ContextBuilder构造函数 与《BuildKernelRunContext》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [BuildTilingContext](build_tiling_context.md)（`same_topic`）：BuildTilingContext 与《ContextBuilder构造函数》的实质衔接是：BuildTilingContext 由 ContextBuilder 的算子名、属性、输入输出和平台信息构造 KernelRunContextHolder；调测页说明如何执行与检查生成的 tiling context。
- [CompileInfo](compile_info.md)（`same_topic`）：CompileInfo 与《ContextBuilder构造函数》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder](context_builder.md)（`same_topic`）：ContextBuilder构造函数 与《ContextBuilder》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [SetOpNameType](set_op_name_type.md)（`same_topic`）：ContextBuilder构造函数 与《SetOpNameType》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
<!-- cannbot:related:end -->
