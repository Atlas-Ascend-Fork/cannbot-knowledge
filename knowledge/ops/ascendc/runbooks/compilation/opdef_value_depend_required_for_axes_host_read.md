---
type: "Runbook"
title: "ValueDepend(REQUIRED) 让 axes 走 host 端"
description: "reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。"
tags: ["task.implementation", "topic.implementation.operator_registration"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# ValueDepend(REQUIRED) 让 axes 走 host 端

## 现象

EuclideanNorm 算子（沿轴归约）的 `axes` 是 Const 输入（reduce 轴索引数组）。在 OpDef 注册（`op_host/euclidean_norm_host.cpp` 的 `REG_OP` / `OpAICoreDef` 块）未对 axes 注明 value 依赖时，aclnn 真机测试中 `axes` tensor 数据留在 device，TilingFunc 在 host 侧 `axesTensor->GetAddr()` 得到 `nullptr`，`ParseAxes` 无法读出 axes 值，回退到 full-reduce（把所有轴当 reduce 轴），导致所有"多 A-lane"（axes 只标部分轴）case 的 TilingData 与 oracle 全 mismatch。

## 适用场景

- **工程形态**：spec / op_host（算子仓 OpDef 注册层，非 kernel 直调）。
- **API 路径**：`OpDef::Input(...).ParamType(REQUIRED).ValueDepend(REQUIRED)`；生成的 `aclnnXxxGetWorkspaceSize` / `aclnnXxxTensorGetWorkspaceSize`；`aclCreateIntArray` / `aclDestroyIntArray`。
- **验证平台与版本**：Ascend950，CANN 9.1.0（x86_64-linux）；aclnn 真机 smoke test + host-only TilingUT。
- **适用粒度**：`operator_family`（所有 reduce 类、带 Const axes/index 输入的算子）。
- **路线优先级**：`recommended_fastpath`（ValueDepend(REQUIRED) 是让 TilingFunc 在 host 读 axes 数据的规范方式）。
- **不适用或未验证场景**：a3/a2 未验证，推断可迁移（OpDef ValueDepend 语义跨平台一致）；axes 本就是 host Const（非 device tensor）时无需 ValueDepend。

## 判别方法

**触发条件**：reduce 类算子的 `axes`（或类似 Const 索引输入）在 OpDef 未注 `ValueDepend`，而 TilingFunc 需要在 host 侧读 axes 数值来决定切分。aclnn 真机测试会暴露 `GetAddr()==nullptr`。

**可执行探针**（在 TilingFunc 里 fprintf axes 的 addr 与 placement）：

```cpp
const gert::Tensor* axesTensor = context->GetInputTensor(AXES_INPUT_INDEX);
fprintf(stderr, "[ParseAxes] axes addr=%p\n", axesTensor->GetAddr());
```

若 `addr=(nil)` 且 TilingFunc 走了"回退 full-reduce"分支，即为未注 ValueDepend 的症状。

**原始观测**（trace seq 3084-3086 reasoning）：

> Adding `ValueDepend(REQUIRED)` changed the aclnn API signature. Now `axes` is `const aclIntArray*` instead of `const aclTensor*`. This means the framework now treats axes as a value-dependent input that's passed as an array of integers, not as a tensor.
>
> With `ValueDepend(REQUIRED)`, the framework generates two API variants:
> 1. `aclnnEuclideanNormGetWorkspaceSize` - takes `const aclIntArray* axes` (value-dependent, data on host)
> 2. `aclnnEuclideanNormTensorGetWorkspaceSize` - takes `const aclTensor* axes` (tensor variant, data on device)

**解释**：`ValueDepend` 的 `Option` 枚举为 `{ IGNORE=0, OPTIONAL=1, REQUIRED=2, DYNAMIC=3, VIRTUAL=4 }`（trace seq 3067 reasoning，据 CANN `op_def.h`）。`REQUIRED` 告诉框架：TilingFunc 必须在 host 拿到 axes 数值（编译期 / 运行期都要），框架会在 TilingFunc 调用前把 device tensor 数据拷到 host。同时框架为同一算子生成两个 aclnn C API：默认变体把 axes 当 `aclIntArray*`（host 数组，调用方直接传值），Tensor 变体把 axes 当 `aclTensor*`（device tensor，框架内部拷）。调用方按 axes 是否已在 host 选变体。

## 验证信号

来源：EuclideanNorm aclnn smoke test + op_host 编译，在 OpDef axes Input 加 `.ValueDepend(REQUIRED)` 后重建。

- 修复前 `axes->GetAddr()=nullptr`，ParseAxes 回退 full-reduce，多 A-lane case TilingData mismatch（来源平台：950；证据等级: tool_observed）
- 修复后 aclnn API 签名变化：`aclnnEuclideanNormGetWorkspaceSize` 的 axes 参数从 `const aclTensor*` 变为 `const aclIntArray*`（来源平台：950；证据等级: tool_observed）
- 框架额外生成 `aclnnEuclideanNormTensorGetWorkspaceSize`（Tensor 变体）（来源平台：950；证据等级: tool_observed）
- TilingFunc 可在 host 读到 axes 数值（来源平台：950；证据等级: tool_observed）

## 预防

- reduce / split / topk 等带 Const 索引输入（axes/k/indices）的算子，若 TilingFunc 要读这些数值决定 tiling，必须在 OpDef 的 Input 上注 `.ValueDepend(REQUIRED)`，不能默认框架会拷数据。
- 加 `ValueDepend(REQUIRED)` 后须同步更新 aclnn 测试调用：默认变体改用 `aclCreateIntArray` 传 `aclIntArray*`，Tensor 场景用 `aclnnXxxTensorGetWorkspaceSize`。

## 失效边界

- 平台：Ascend950 / CANN 9.1.0 实测；a3/a2 未验证，推断可迁移。
- 边界：本卡仅覆盖 `ValueDepend(REQUIRED)` 的正确用法与 API 变体生成行为；同一轨迹中，axes 改为 `ValueDepend(OPTIONAL)` 后，即使 TilingFunc 是纯 stub，真机 ACLNN 仍抛 `std::bad_alloc`，因此二者不可互换。

## 误诊

无。

<!-- cannbot:related:start -->
## 相关

- [Input（OpDef）](../../apis/utils_api/prototype_register_management/op_def/input.md)（`exemplifies`）：焦点处理OpDef Input 的参数类型、格式、可选性和值依赖配置；ValueDepend(REQUIRED) 让 axes 走 host 端正文说明“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) ”。候选配置 Input 返回的 OpParamDef，或复现输入可选性、格式和值依赖造成的框架故障。
- [Input（原型注册管理）](../../apis/utils_api/prototype_register_management/op_ai_core_config/input.md)（`exemplifies`）：《Input（原型注册管理）》处理“某些场景下，同一个算子在不同的AI处理器型号上，其支持的原型输入不同。 通过该接口，可针对不同的AI处理器型号注册差异化的算子原型。调用该接口后会返回一个OpParamDef结构，后续可通过该结构配置算子输入信息。”。《ValueDepend(REQUIRED) 让 axes 走 host 端》明确“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”，可直接用于核对算子 Input/Output 原型、OpParamDef dtype/format/optional/value-depend 参数及已证注册故障。
- [OpDef](../../apis/utils_api/prototype_register_management/op_def/op_def.md)（`exemplifies`）：ValueDepend(REQUIRED) 让 axes 走 host 端说明reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。
- [SetTiling（OpAICoreDef）](../../apis/utils_api/prototype_register_management/op_ai_core_def/set_tiling.md)（`exemplifies`）：SetTiling（OpAICoreDef） 与《ValueDepend(REQUIRED) 让 axes 走 host 端》的实质衔接是：SetTiling 作用于 OpAICoreDef 的 tiling 对象，TilingParse 空与 ValueDepend 轴错误是 host tiling 注册阶段的直接失败模式。
- [ValueDepend](../../apis/utils_api/prototype_register_management/op_param_def/value_depend.md)（`exemplifies`）：《ValueDepend》给出“标识该输入是否为“数据依赖输入”，数据依赖输入是指在Tiling/InferShape等函数实现时依赖该输入的具体数据。该输入数据为host侧数据，开发者在Tiling函数/InferShape函数中可以通过TilingContext类的GetInputTensor/InferShapeContext类的GetInputTensor获取这个输入数据。”；该约束/探针可直接复现、解释或前置验证《ValueDepend(REQUIRED) 让 axes 走 host 端》中的“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”。
- [原型注册接口（OP_ADD）](../../apis/utils_api/prototype_register_management/op_add.md)（`exemplifies`）：《原型注册接口（OP_ADD）》处理“注册算子的原型定义，从而确保算子能够被框架正确识别、编译和执行。 算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型（自定义算子类的类名），进行算子原型注册。详细内容请参考算子原型定义。”。《ValueDepend(REQUIRED) 让 axes 走 host 端》明确提供“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”，其参数、调用或验证步骤直接接入OP_ADD 宏与 OpDef、注册函数、原型库和注册故障的可执行闭环。
- [StorageShape scalar GetShapeSize 返回 1](gert_storage_shape_scalar_getshapesize_returns_one.md)（`related`）：《StorageShape scalar GetShapeSize 返回 1》明确“空 axes 表示为 rank-0 scalar tensor 时 GetShapeSize() 返回 1（非 0），TilingFunc 误判 axesNum=1 并读 nullptr 数据；须用 GetDimNum()==0 检测 empty axes。”；它与《ValueDepend(REQUIRED) 让 axes 走 host 端》的“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”在实际调用参数、数据流或结果校验上直接衔接。
- [tiling 按位置奇偶判 reduce 轴致非交替 axes 误减](../precision/tiling_reduce_axes.md)（`related`）：focal 的错误是按 axes 位置奇偶猜归约维；目标卡给出正路径：在 OpDef 对 axes 配 ValueDepend(REQUIRED)，让 Host Tiling 读取真实轴值并生成对应 aclIntArray/Tensor API。
- [缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape](op_proto_lib_axes_infershape.md)（`related`）：《缺 OP_PROTO_LIB 致空 axes 命中内置 InferShape》的任务是“cust_proto_obj 未加 OP_PROTO_LIB 时 OP_ADD 走默认分支，自定义 V2 gert InferShape 不注入 rt2 registry，框架回落 CANN 内置 EuclideanNormInferShape（reduce_ops.cc），全局 first-wins 使 COMMON_INFER_FUNC_REG 无法覆盖；内置把空 axes(shape=[0]) 当 passthrough 而非 full reduce，输出 shape 错误。”。《ValueDepend(REQUIRED) 让 axes 走 host 端》具体提供“reduce 类算子的 axes Input 在 OpDef 注册时加 .ValueDepend(REQUIRED)，框架会把 device 数据拷到 host 供 TilingFunc 读取，并生成 aclnnXxxGetWorkspaceSize(aclIntArray*) 与 aclnnXxxTensorGetWorkspaceSize(aclTensor*) 两个 API 变体。”，它直接用于OP_PROTO_LIB、OP_ADD 和 InferShape 注册路由对空 axes shape 的影响。
- [TilingFunc 未声明依赖读 axes 致 segfault](tilingfunc_axes_segfault.md)（`same_topic`）：两卡构成同一 axes host-read 契约的失败与正向落地：本卡证明未声明依赖直接 GetData 会 segfault，目标卡证明 OpDef 加 ValueDepend(REQUIRED) 后框架下发值且 TilingFunc 可读。
<!-- cannbot:related:end -->
