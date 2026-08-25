---
type: "Runbook"
title: "optional input 未连接触发 InferShape 失败"
description: "OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。"
tags: ["task.debugging", "topic.implementation.operator_registration"]
status: stable
sources: []
created_at: "2026-08-18T12:30:47Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# optional input 未连接触发 InferShape 失败

## 现象

在 Ascend950PR（CANN 9.0.0）上用 GEIR 测试程序调用 `advance_step`（已补 Output 声明、kernel 签名、buffer 拷贝），`RunGraph` 仍在 InferShape pass 失败。报错原文（GE 工具输出，verbatim）：

```text
E19999[PID: 647236] 2026-08-06-15:04:23.258.077 (E19999):  Assert ((ConstructCompileKernelContextInputs(op, op_desc, inputs, ge_tensors_holder)) == ge::GRAPH_SUCCESS) failed[FUNC:ConstructInferShapeContextInputs][FILE:shape_inference.cc][LINE:180]
        TraceBack (most recent call last):
       [Construct][InferShapeContextInputs] failed, op_desc[AdvanceStep][FUNC:InferShapeOnCompile][FILE:shape_inference.cc][LINE:658]
       Call InferShapeAndType for node:AdvanceStep(AdvanceStep) failed. You can ignore this validation by exporting IGNORE_INFER_ERROR=1 if necessary, but it is highly recommended to fix this problem.[FUNC:CallInferFunc][FILE:op_desc_utils_ex.cc][LINE:183]
       ...
       Run graph failed, error code:1343242270, session_id:0, graph_id:0.[FUNC:RunGraph][FILE:ge_api.cc][LINE:575]
```

失败发生在 InferShape 函数被调用**之前**的 context 构造阶段（`ConstructInferShapeContextInputs`），即不是 `advance_step_infershape.cpp` 的实现问题，而是 GE 框架构造 context 时 input 数量与 OpDef 声明不匹配。

## 适用场景

- **工程形态**：op_host OpDef 注册 + GEIR 通路测试（`ge::Session`/`AddGraph`/`RunGraph`）。
- **API 路径**：`OpDef` 的 `this->Input(...).ParamType(OPTIONAL)` 声明 + GE `ConstructInferShapeContextInputs`（`shape_inference.cc:180`）。
- **验证过的平台与 CANN 版本**：Ascend950PR / CANN 9.0.0。
- **适用粒度**：`operator_family`（任何 OpDef 声明 optional input、且 GEIR 测试图未连接该 optional input 的算子均会复现）。
- **路线优先级**：`diagnostic_only`。本卡只定位 context 构造阶段的输入契约不一致，不提供跳过 InferShape 校验的绕过路线。
- **不适用/未验证场景**：aclnn 通路不经 InferShape pass，本卡不适用；连接 optional input 会触发 forward compatibility 错误（见误诊），不是解法。

## 判别方法

**触发条件**：OpDef 声明的 input 数 > GEIR 图实际连接的 input 数（典型：声明了 optional input 但测试图只连 required input）。

**可执行探针**：查安装目录下算子配置的 `optionalInputMode` 与 input 列表（工具输出，verbatim）：

```text
=== 950 config ===
optionalInputMode: gen_placeholder
inputs: 8
  input_tokens: required
  sampled_token_ids: required
  input_positions: required
  seq_lens: required
  slot_mapping: required
  block_tables: required
  spec_token: optional
  accepted_num: optional
```

`optionalInputMode: gen_placeholder` 说明 GE 设计上会为未连接的 optional input 生成 placeholder，但 `ConstructInferShapeContextInputs` 仍按声明的 8 个 input 构造 context，与实际连接的 6 个不一致 → assert 失败。

**原始观测**：`RunGraph` 报 `ConstructInferShapeContextInputs ... shape_inference.cc:180` assert 失败，且报错明示 `You can ignore this validation by exporting IGNORE_INFER_ERROR=1`。

**解释边界**：日志表明失败发生在真正的 InferShape 回调之前，因此修改该回调不能触及当前失败点。声明 8 个 input、图中连接 6 个 input 是直接可核的差异；至于 placeholder 生成与内置算子定义覆盖如何共同影响 context 构造，本 trace 没有隔离到框架内部的唯一机制。

## 验证信号

- 不带 `IGNORE_INFER_ERROR`，`RunGraph` 在 InferShape pass 失败、报 `ConstructInferShapeContextInputs ... shape_inference.cc:180` assert，error code 1343242270（来源平台：950；证据等级：tool_observed）。
- 探针读取 950 算子配置，确认 `optionalInputMode: gen_placeholder`、声明 8 input（6 required + spec_token/accepted_num 2 optional），与测试图连接的 6 个 input 不匹配（来源平台：950；证据等级：tool_observed）。

## 失效边界

- ascend910b / ascend910_93：未验证，推断可迁移（同一 GE 框架的 `ConstructInferShapeContextInputs` 机制）。
- 连接 optional input 试图"对齐 8 input"会触发 forward compatibility 错误（见误诊），不可行。

## 误诊

- **误诊 A：去掉 `.Version(ADVANCE_STEP_VERSION_TWO)` 声明以让 optional input 在 v1 可用**。尝试后 `ConstructInferShapeContextInputs` 仍失败——根因不在 Version 声明，而在框架层 input 数量不匹配。
- **误诊 B：在 GEIR 测试图中连接全部 8 个 input（含 spec_token/accepted_num）**。尝试后出现独立的 `forward compatibility` 错误，说明该对照没有验证 optional-input 缺失问题；内置与自定义定义的加载优先级需另行核实。
- **误诊 C：修改 `advance_step_infershape.cpp` 处理 optional 缺失**。无效——失败在 `ConstructInferShapeContextInputs`（context 构造阶段），InferShape 函数根本未被调用到。

<!-- cannbot:related:start -->
## 相关

- [EnableFallBack](../../apis/utils_api/prototype_register_management/op_def/enable_fall_back.md)（`exemplifies`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；optional input 未连接触发 InferShape 失败正文界定“OpDef 声明含 optional input、GEIR 图未连接该 input 时，GE 在 InferShape pass 的 ConstructInferShapeContextInputs 阶段 assert 失败，算子 Infe”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [Follow（OpParamDef）](../../apis/utils_api/prototype_register_management/op_param_def/follow.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《Follow（OpParamDef）》明确提供“用于指定当前输入/输出的datatype/format/shape信息与之前定义过的某个输入一致。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [Inputs（Utils API）](../../apis/utils_api/tiling_tuning/context_builder/inputs.md)（`exemplifies`）：《Inputs（Utils API）》说明将void\ 指针的vector设置为KernelContext的inputs；《optional input 未连接触发 InferShape 失败》说明OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。。二者在Inputs写入ContextBuilder的KernelContext输入，AddInputTd、holder及Build*Context决定描述和构造顺序上存在可执行的直接衔接。
- [Input（OpDef）](../../apis/utils_api/prototype_register_management/op_def/input.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《Input（OpDef）》明确提供“注册算子输入，调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [Input（原型注册管理）](../../apis/utils_api/prototype_register_management/op_ai_core_config/input.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《optional input 未连接触发 InferShape 失败》明确“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpDef](../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《OpDef》明确提供“OpDef算子定义接口索引。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [ParamType（OpParamDef）](../../apis/utils_api/prototype_register_management/op_param_def/param_type.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《ParamType（OpParamDef）》明确提供“OpParamDef &ParamType(Option param_type)”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [SetInferShape](../../apis/utils_api/prototype_register_management/op_def/set_infer_shape.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《SetInferShape》明确提供“使用图模式时，需要调用该接口注册Shape推导函数。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [SetInferShapeRange](../../apis/utils_api/prototype_register_management/op_def/set_infer_shape_range.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《SetInferShapeRange》明确提供“使用图模式时，需要调用该接口注册ShapeRange推导函数。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [原型注册接口（OP_ADD）](../../apis/utils_api/prototype_register_management/op_add.md)（`exemplifies`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《原型注册接口（OP_ADD）》明确提供“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
- [advance_step in-place kernel FATBIN wrap](fatbin_wrapper_param_count_matches_opdef_input_plus_output.md)（`related`）：optional input 卡说明 OpDef 声明会改变框架生成的输入上下文；与本卡共同强调 wrapper/上下文严格服从 OpDef 参数契约。
- [基本开发流程](../../guides/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md)（`related`）：基本开发流程 与《optional input 未连接触发 InferShape 失败》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [如何开发动态输入算子](../../guides/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md)（`related`）：如何开发动态输入算子 与《optional input 未连接触发 InferShape 失败》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [算子原型定义](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`related`）：《optional input 未连接触发 InferShape 失败》处理“OpDef 声明含 optional input、GEIR 图未连接该 input 时，本例在 ConstructInferShapeContextInputs 阶段 assert；用于确认失败发生在算子 InferShape 回调之前，并核对声明输入与实际连边。”。《算子原型定义》明确提供“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，其参数、调用或验证步骤直接接入可选输入在 OpDef/原型/InferShape/InferShapeRange 中的上下文合同。
<!-- cannbot:related:end -->
