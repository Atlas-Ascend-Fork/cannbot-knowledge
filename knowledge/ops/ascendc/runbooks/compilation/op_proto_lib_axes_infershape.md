---
type: "Runbook"
title: "缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape"
description: "cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。"
tags: ["task.debugging", "topic.implementation.operator_registration"]
status: stable
sources: []
created_at: "2026-08-18T16:10:11Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["empty_axes", "full_reduce"]
---

# 缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape

## 现象

在 Ascend950（arch35, CANN 9.0.0-beta.2）上以 GEIR 图模式开发 `EuclideanNorm` 算子。GEIR ST 静态用例 T-S10（"special_fullreduce"——空 axes(shape=[0]) 应做 full reduce，输入 x shape=[2,3] 时期望输出 shape=[]）持续失败：输出 shape 不是 full reduce 的结果，而是 passthrough（原输入 shape=[2,3]）。`GRAPH-RUN` 行报告 `value=FAIL`，`GEIR-SUMMARY total=35 pass=34 fail=1`。

## 适用场景

- **工程形态**：aclnn/GEIR 图模式算子开发（op_host + op_graph 注册层），属 op_host 构建配置 + InferShape 注册机制问题，非 kernel 计算逻辑。
- **API 路径**：CMake `target_compile_definitions(cust_proto_obj PRIVATE OP_PROTO_LIB ...)` + `OP_ADD`/`OP_END_FACTORY_REG` + `Operator::InferFuncRegister` + `COMMON_INFER_FUNC_REG` + gert V2 `IMPL_OP` InferShape/InferDataType。
- **验证平台与版本**：Ascend950，CANN 9.0.0-beta.2，GEIR 图模式 ST（test_geir）。
- **适用粒度**：`operator_family` —— 任何自定义算子名与 CANN 内置算子同名（EuclideanNorm 等 reduce 类内置）、或需要覆盖内置 InferShape 行为的算子都会踩。
- **不适用或未验证场景**：算子名不与任何 CANN 内置冲突、且自定义 InferShape 无需覆盖内置时不触发；非 GEIR/图模式路径不涉及。a2/a3 平台未验证。

## 判别方法

### 触发（tool_observed 失败）

GEIR ST 静态用例 T-S10（空 axes shape=[0]，输入 x shape=[2,3]，keep_dims=false 期望 full reduce 输出 shape=[]）在 `GRAPH-RUN mode=static` 下 `value=FAIL`：`expected_shape=[] actual_shape=[2,3] expected_numel=1 actual_numel=6`。即框架对空 axes 做了 passthrough（输出原 shape）而非 full reduce。`GEIR-SUMMARY total=35 pass=34 fail=1`。

### 探针（可执行检查）

1. **路由日志检查**：抓 GEIR 运行日志，grep `CallInferFunc` 与 `InferShapeFuncV`，看 T-S10 节点命中的是自定义 InferShape 还是 built-in。命中 `InferShapeFuncV1` 且不是开发者注册的自定义 V1 时，说明落到了 built-in。
2. **built-in 符号检查**：对 CANN built-in `libopsproto.so` 跑 `strings | grep <OpType>InferShape` 与 `nm -D | grep op_impl_register_infershape_<OpType>`，确认 built-in 是否为同名算子注册了 InferShape（若存在同名符号，全局 map 已被 built-in 先占）。
3. **shape flow 检查**：抓 T-S10 节点的 `infer_base_pass`/`infershape_pass` 日志，看 axes shape=[0] 时 `[after_infer]` 输出 shape 是否被改成 passthrough（与输入同 shape），并核对 `origin shape` 是否未被 reduce。

### 观测（tool_observed）

- `GRAPH-RUN ... case=T-S10 ... expected_shape=[] actual_shape=[2,3] ... value=FAIL` / `CASE T-S10 FAIL` / `GEIR-SUMMARY total=35 pass=34 fail=1`。
- `strings libopsproto.so` 命中 `EuclideanNormInferShape` 与 `Enter EuclideanNormInferShape proto inferfunction`；`nm -D` 命中 `ops::op_impl_register_infershape_EuclideanNorm`（built-in 已在全局 map 注册同名 InferShape）。
- T-S10 shape flow：`[before_infer]` axes output shape=[0]；`[after_infer]` 节点 output shape=[2,3]、`origin shape is 6`（即未 reduce，passthrough）。

### 解释（根因分析）

两层机制叠加：

1. **`cust_proto_obj` 未定义 `OP_PROTO_LIB`**：标准 CANN 模板（`npu_op_library` GRAPH 编译源时）会给 proto 目标加 `OP_PROTO_LIB`，使 `OP_ADD` 经 `OpImplRegisterV2` 把 OpDef 上 `SetInferShape`/`SetInferDataType` 注册的 gert V2 InferShape 注入 rt2 registry。未加时 `OP_ADD` 走默认分支（仅 OpDefFactory），V2 gert InferShape 永不注入 rt2 registry，框架回落到 built-in V1 `InferShapeAndType`。
2. **全局 `COMMON_INFER_FUNC_REG` 是 first-wins**：CANN built-in `EuclideanNormInferShape`（reduce_ops.cc）先注册到全局 `InferShapeFuncRegister` map，自定义算子用 `COMMON_INFER_FUNC_REG` 后注册无法覆盖（first-wins，后注册不生效）。built-in 对空 axes（shape=[0]）按 passthrough 处理，而非 full reduce。

判别要点：当且仅当「自定义算子名与 CANN built-in 同名」且「cust_proto_obj 缺 OP_PROTO_LIB 或仅靠 COMMON_INFER_FUNC_REG 注册」两个条件同时成立时，空 axes（及任何依赖自定义 InferShape 语义的用例）会落到 built-in 而失败。仅命中 built-in 符号（探针 2）但自定义 InferShape 已通过 `Operator::InferFuncRegister` 逐实例挂到 OpDesc 时，`CallInferFunc` 优先查 OpDesc 上的 InferFunc（先于全局 map），可不触发本失败。

## 验证信号

- T-S10 `GRAPH-RUN mode=static` 报告 `value=FAIL`：`expected_shape=[] actual_shape=[2,3] expected_numel=1 actual_numel=6`，`GEIR-SUMMARY total=35 pass=34 fail=1`（来源平台:950；证据等级:tool_observed）。
- `strings libopsproto.so` 与 `nm -D` 输出含 built-in `EuclideanNormInferShape`、`op_impl_register_infershape_EuclideanNorm` 符号，证明同名 built-in InferShape 已全局注册（来源平台:950；证据等级:tool_observed）。
- T-S10 shape flow 日志：axes output shape=[0]，`[after_infer]` 节点 output shape=[2,3]、`origin shape is 6`（passthrough，未 reduce）（来源平台:950；证据等级:tool_observed）。

<!-- cannbot:related:start -->
## 相关

- [EnableFallBack](../../apis/utils_api/prototype_register_management/op_def/enable_fall_back.md)（`exemplifies`）：焦点处理OpDef fallback 对 Input/Output 与 InferShape/InferDataType 的依赖；缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape正文界定“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferSha”。候选配置 fallback 必需的 OpDef 输入输出和推导函数，或复现缺推导/原型库造成的真实下发故障。
- [OpDef](../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《OpDef》具体提供“OpDef算子定义接口索引。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [SetInferDataType](../../apis/utils_api/prototype_register_management/op_def/set_infer_data_type.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《SetInferDataType》具体提供“使用图模式时，需要调用该接口注册DataType推导函数。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [SetInferShape](../../apis/utils_api/prototype_register_management/op_def/set_infer_shape.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《SetInferShape》具体提供“使用图模式时，需要调用该接口注册Shape推导函数。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [SetInferShapeRange](../../apis/utils_api/prototype_register_management/op_def/set_infer_shape_range.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《SetInferShapeRange》具体提供“使用图模式时，需要调用该接口注册ShapeRange推导函数。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [原型注册与管理](../../apis/utils_api/prototype_register_management/prototype_register_management.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《原型注册与管理》具体提供“算子原型注册与管理接口索引。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [原型注册接口（OP_ADD）](../../apis/utils_api/prototype_register_management/op_add.md)（`exemplifies`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《原型注册接口（OP_ADD）》具体提供“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [ACLNN 507035 — opType 与内置 ops_legacy 同名碰](aclnn_optype_collision_built_in_ops_legacy_507035.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《ACLNN 507035 — opType 与内置 ops_legacy 同名碰》具体提供“CANN C++ 运行时 AppendDynBin/HashAndInsert 在同名时优先加载 built-in ops_legacy kernel binary 而非 vendor，导致 vendor TilingData 与内置 kernel 结构不匹配触发 vector core exception 507035；修复为 opType 重命名加 Custom 后缀。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [InferShape 返回 identity 致空 kernel 假通过](../precision/infershape_identity_kernel.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《InferShape 返回 identity 致空 kernel 假通过》具体提供“op_host InferShape 用 *output=*input 占位时，aclnn 框架对 identity 用例走旁路 copy，空 kernel 也有用例通过，掩盖 kernel 未输出的缺陷。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [ValueDepend(REQUIRED) 让 axes 走 host 端](opdef_value_depend_required_for_axes_host_read.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《ValueDepend(REQUIRED) 让 axes 走 host 端》具体提供“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [aclnn 黑盒 numel 不符：输出取自 CSV y 不被算子覆盖](../precision/aclnn_numel_csv_y.md)（`related`）：aclnn 黑盒 numel 不符：输出取自 CSV y 不被算子覆盖 与《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的实质衔接是：该 ACLNN numel 误判来自输出 shape/测试数据来源；L0 shape、白盒绕过、identity InferShape、OP_PROTO_LIB 和 output view 卡提供同层判别。
- [基本开发流程](../../guides/programming_guide/advanced_programming/operator_graph_development/basic_development_flow.md)（`related`）：基本开发流程 与《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的实质衔接是：算子图基本流程把 OpDef 原型、InferShape/InferDataType、图编译执行和 tiling 下沉串成同一生命周期；三个失败案例分别验证原型加载、可选输入和 shape 推导不能被绕过。
- [如何开发动态输入算子](../../guides/programming_guide/appendix/common_operations/develop_dynamic_input_operator.md)（`related`）：如何开发动态输入算子 与《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的实质衔接是：动态输入必须在原型侧声明动态 Input，在 host/kernel 间用 ListTensorDesc/TensorDesc 与 TensorList 传递；动态编译和 InferShape/optional input 案例限定完整开发链。
- [算子原型定义](../../guides/programming_guide/advanced_programming/aclnn_operator_development/design_and_implementation/operator_prototype_definition.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《算子原型定义》具体提供“本文属于基础内容，介绍如何通过算子原型定义描述算子对外暴露的接口和支持范围。本文承接算子功能设计的结论，说明如何将功能设计中的输入输出、属性、dtype/format和Tiling函数关联落地为OpDef代码，并介绍图模式下的输出shape和dtype推导配置。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
<!-- cannbot:related:end -->
