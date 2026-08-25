---
type: Guide
title: 算子原型定义
description: 本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
tags: [task.lookup, topic.programming_model]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---
# 算子原型定义

本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
## 原型定义放在哪里
在AddCustom样例工程中，算子原型定义位于Host侧实现文件：
该文件中同时包含三类内容：
内容：作用
TilingFunc：Host侧Tiling函数，负责计算Kernel启动和分块参数
InferShape、InferDataType：图模式下的输出shape和dtype推导函数，仅在需要支持图模式时编写
class AddCustom : public OpDef：算子原型定义，描述输入、输出、属性、Tiling关联
本文重点讲class AddCustom : public OpDef中的原型定义内容，同时说明它和Tiling函数之间的连接关系，并补充图模式下关联推导函数的方法。
## 定义OpDef类并注册算子
算子原型通过一个继承自OpDef的C++类承载。类名通常与算子类型保持一致。AddCustom的算子类型为AddCustom，因此定义AddCustom类。
这里有两个关键点：
- 构造函数通过OpDef(name)初始化基类，后续的Input、Output、Attr、AICore等声明都写在构造函数中。
- 文件末尾通过OP_ADD(AddCustom)注册算子类型，编译工具据此识别算子原型，并生成aclnn接口、图模式原型等相关代码。
## 定义输入和输出
输入输出定义来自功能设计阶段的结论。AddCustom有两个输入x、y，一个输出z，三个Tensor共同表达z = x + y的计算语义，因此都声明为REQUIRED。基础样例没有属性，输入输出声明就是原型定义中最先落地的接口内容。
输入输出参数说明如下：
原型项：参数：作用
Input/Output：输入输出名称：声明输入输出名称，名称需要和功能设计中的参数名称一致。声明顺序会影响aclnn接口参数顺序和Kernel入口参数顺序。
Input/Output：ParamType：声明参数提供方式。REQUIRED表示每次调用都必须提供，OPTIONAL表示部分场景可以省略，DYNAMIC表示数量随调用变化。
Input/Output：DataType：声明输入输出支持的dtype。多个dtype按列表顺序和format列表一一对应。
Input/Output：Format：声明输入输出支持的format。多个format按列表顺序和dtype列表一一对应。
同一个输入或输出支持多组dtype/format时，DataType和Format列表需要按位置对应。例如下面的写法表示支持DT_FLOAT16 + FORMAT_ND、DT_FLOAT + FORMAT_ND和DT_INT32 + FORMAT_ND三组组合。

<!-- cannbot:related:start -->
## 相关

- [AICore（OpDef）](../../../../../apis/utils_api/prototype_register_management/op_def/ai_core.md)（`explains`）：指南通过 AICore 关联 TilingFunc 与 AI Core 配置，把外部接口描述接到执行实现。
- [Attr（OpDef）](../../../../../apis/utils_api/prototype_register_management/op_def/attr.md)（`explains`）：原型定义指南展示 Attr 如何与输入输出、dtype/format、TilingFunc 一起落到 OpDef 构造函数，并说明声明顺序和生成接口的关系。
- [DataTypeForBinQuery](../../../../../apis/utils_api/prototype_register_management/op_param_def/data_type_for_bin_query.md)（`explains`）：DataTypeForBinQuery 与《算子原型定义》的实质衔接是：DataTypeForBinQuery 与 FormatForBinQuery 共同决定运行时二进制键；OpParamDef 的类型/格式列表、Version、Input 及 InferDataType 必须保持注册与推导一致。
- [Input（OpDef）](../../../../../apis/utils_api/prototype_register_management/op_def/input.md)（`explains`）：原型指南中的输入名称、必选性、dtype 与 format 组合由 OpDef Input 接口具体声明。
- [Input（原型注册管理）](../../../../../apis/utils_api/prototype_register_management/op_ai_core_config/input.md)（`explains`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《算子原型定义》明确“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpAttrDef](../../../../../apis/utils_api/prototype_register_management/op_attr_def/op_attr_def.md)（`explains`）：OpAttrDef 与《算子原型定义》的实质衔接是：OpAttrDef 定义属性名、类型、OPTIONAL/REQUIRED、默认值和 Version；Comment 生成原型注释，OpDef::Attr 挂载属性，Host TilingData 传递与缓存故障说明 runtime 属性进入 kernel 时的后续契约。
- [OpDef](../../../../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`explains`）：算子原型定义说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
- [Output（OpDef）](../../../../../apis/utils_api/prototype_register_management/op_def/output.md)（`explains`）：输出声明顺序会影响 aclnn 与 Kernel 参数顺序，OpDef Output 是该契约的落地接口。
- [SetInferShape](../../../../../apis/utils_api/prototype_register_management/op_def/set_infer_shape.md)（`explains`）：图模式输出 shape 推导需要在 OpDef 上注册 InferShape 回调，该接口完成关联。
- [原型注册与管理](../../../../../apis/utils_api/prototype_register_management/prototype_register_management.md)（`explains`）：《算子原型定义》给出“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”；该约束/探针可直接复现、解释或前置验证《原型注册与管理》中的“算子原型注册与管理接口索引。”。
- [原型注册接口（OP_ADD）](../../../../../apis/utils_api/prototype_register_management/op_add.md)（`explains`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《算子原型定义》明确提供“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [optional input 未连接触发 InferShape 失败](../../../../../runbooks/compilation/optional_input_infershape.md)（`related`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《算子原型定义》明确提供“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [基本开发流程](../../operator_graph_development/basic_development_flow.md)（`related`）：基本开发流程 与《算子原型定义》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [算子功能设计](operator_function_design.md)（`related`）：《算子功能设计》说明本文属于基础内容，介绍在编写自定义算子代码前需要完成的功能设计，包括将计算语义转换为工程实现，以及明确需要编写的工程文件。；《算子原型定义》说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。二者在功能设计明确拆成原型、Host Tiling和Kernel三类代码，后续章节分别落实属性、多分支、输出shape、编译部署与快速入门上存在可执行的直接衔接。
- [算子基本概念](../../../../technical_appendix/concepts_and_terms/neural_networks_and_operators/operator_basics.md)（`related`）：算子基本概念：算子名称/类型/Tensor/Shape/Layout概念是原型定义和功能设计的输入语言；数据排布卡进一步解释Tensor layout，帮助把概念落到注册与实现。 目标卡《算子原型定义》补充：本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](../../../../../runbooks/compilation/op_proto_lib_axes_infershape.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《算子原型定义》具体提供“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [高级编程基本流程](kernel_operator_implementation.md)（`related`）：《高级编程基本流程》说明本文属于基础内容，介绍aclnn工程化算子开发方式中Kernel侧的基本接入流程，重点说明Kernel入口函数格式、参数顺序、TilingData处理和编译期信息获取方式。Global Memory地址绑定、UB管理、数据搬运、计算和同步等Kernel核心实现方法，请参考核函数。；《算子原型定义》说明本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。二者在Kernel侧基本接入的参数顺序、TilingData和编译期信息必须与原型、Host Tiling、编译部署及动态输入设计一致上存在可执行的直接衔接。
- [如何开发动态输入算子](../../../appendix/common_operations/develop_dynamic_input_operator.md)（`same_topic`）：如何开发动态输入算子 与《算子原型定义》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [通过TilingData传递属性信息](tiling_data_attributes.md)（`same_topic`）：“通过TilingData传递属性信息”处理本文属于扩展内容，介绍算子属性参与Kernel计算时所需的数据传递方法。算子属性在Host侧保存，Kernel不能直接读取。属性需要参与Kernel计算时，Host侧Tiling函数先读取属性值，再把Kernel真正需要的数据写入TilingD…；“算子原型定义”明确本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。。实质衔接：属性从 OpDef 声明，经 Host Tiling 读取并写入注册的 TilingData，再由 Kernel 宏解析；故障卡验证类型契约与跨调用缓存边界。
- [高级编程基本流程](host_tiling_implementation.md)（`same_topic`）：高级编程基本流程 与《算子原型定义》的实质衔接是：Host tiling 把 shape/属性/场景写成 TilingData、numBlocks、workspace 与 TilingKey；设计、原型、构建和 tilingKey 路由故障共同覆盖完整工程链。
<!-- cannbot:related:end -->
