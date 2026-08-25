---
type: API
title: OpDef
description: OpDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpDef/OpDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# OpDef

OpDef 是算子原型定义的核心类，用于声明算子的输入（Input）、输出（Output）、属性（Attr）以及 Shape 与数据类型推导函数（SetInferShape、SetInferShapeRange、SetInferDataType）。通过 AICore、AICPU、HostCPU、MC2 子配置指定算子的执行引擎，并支持 Fallback 机制（EnableFallBack）、格式匹配模式（FormatMatchMode）和注释（Comment）。

<!-- cannbot:related:start -->
## 相关

- [ACLNN 561000 非连续张量需 AutoContiguous](../../../../runbooks/compilation/aclnn_561000_autocontiguous.md)（`exemplifies`）：ACLNN 561000 非连续张量需 AutoContiguous 与《OpDef》的实质衔接是：561000 来自 OpParamDef 未声明连续性策略；AutoContiguous/IgnoreContiguous、Input/OpDef 和非连续 Load/Store/Slice/Transpose 卡共同决定转换还是保留 strides。
- [OpDef FORMAT_NCHW 致 5D 报 161002](../../../../runbooks/compilation/opdef_format_nchw_5d_161002.md)（`exemplifies`）：OpDef FORMAT_NCHW 致 5D 报 161002说明同时支持 4D/5D 的算子在 OpDef 注册 FORMAT_NCHW 会让 5D 张量在 GetWorkspaceSize 阶段报 ACLNN error 161002；NCHW 只对 4D 有效，该路线 banned，应保持 FORMAT_ND 并由 tiling 据 shape 推断布局。
- [ValueDepend(REQUIRED) 让 axes 走 host 端](../../../../runbooks/compilation/opdef_value_depend_required_for_axes_host_read.md)（`exemplifies`）：ValueDepend(REQUIRED) 让 axes 走 host 端说明reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。
- [aclnn_exclude 头文件自动生成覆盖源码致签名不符](../../../../runbooks/compilation/aclnn_exclude.md)（`exemplifies`）：OpDef 属性列表是 autogen 头文件签名的源契约。
- [optional input 未连接触发 InferShape 失败](../../../../runbooks/compilation/optional_input_infershape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《OpDef》明确提供“OpDef算子定义接口索引。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《OpDef》具体提供“OpDef算子定义接口索引。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [基本开发流程](../../../../guides/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md)（`explains`）：基本开发流程 与《OpDef》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [算子原型定义](../../../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`explains`）：算子原型定义说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
- [Attr（OpDef）](attr.md)（`related`）：OpDef 核心类用 Input、Output 与 Attr 声明算子外部契约，Attr 是其中的属性注册成员。
- [Output（OpDef）](output.md)（`related`）：“Output（OpDef）”定义：注册算子输出，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输出信息。；“OpDef”定义：OpDef算子定义接口索引。。实质衔接：Output 与 Input 建立 OpDef 参数契约，随后 shape/dtype 推导回调决定输出元信息；OpDef 总览给出注册链。
- [原型注册接口（OP_ADD）](../op_add.md)（`related`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《OpDef》明确提供“OpDef算子定义接口索引。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [Comment](comment.md)（`same_topic`）：OpDef 入口把 Comment 列为算子原型定义能力，与 Input/Output/Attr、推导函数和执行引擎配置共同生成原型。
- [EnableFallBack](enable_fall_back.md)（`same_topic`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；OpDef正文界定“OpDef算子定义接口索引”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
<!-- cannbot:related:end -->
