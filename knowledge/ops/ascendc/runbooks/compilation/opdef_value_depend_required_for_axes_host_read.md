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