---
type: "Runbook"
title: "561002：TilingParse 未生效，CompileInfo 为空"
description: "在 npu_op_library（cmake）构建系统中 IMPL_OP_OPTILING.TilingParse 注册不触发回调，runtime GetCompileInfo 返回 null 致 561002；诊断后回退 GetPlatformInfo 直读平台信息。"
tags: ["task.debugging", "topic.tiling", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-18T07:24:32Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 561002：TilingParse 未生效，CompileInfo 为空

## 现象

在开发 softplus_v2_grad 算子（ACLNN 框架，ops-registry-invoke 工作流）时，开发者把 tiling 注册从 OpDef 中的 `SetTiling` 迁移到 `IMPL_OP_OPTILING(SoftplusV2Grad).Tiling(...).TilingParse<SoftplusV2GradCompileInfo>(...)` 模式后，smoke test 在 `aclnnSoftplusV2GradGetWorkspaceSize` 调用处返回 ACLNN 错误码 561002（`ACLNN_ERR_INNER_TILING_ERROR`）。迁移前 smoke test 3/3 全部通过，迁移后全部失败。构建本身（`./build.sh softplus_v2_grad_package`）成功退出码 0，kernel binary 正常生成，但 runtime tiling 函数返回 `GRAPH_FAILED`。

## 适用场景

- **工程形态**：ACLNN 算子仓开发（ops-registry-invoke），op_host 侧 tiling 实现，npu_op_library（cmake）构建系统。
- **API 路径**：`IMPL_OP_OPTILING(OpType).Tiling(...).TilingParse<T>()` 注册 → runtime `TilingFunc*(gert::TilingContext*)` → `GetCompileInfo<T>()` 读取编译期写入的 CompileInfo。
- **验证过的平台与 CANN 版本**：Ascend950，CANN 9.1.0（`/home/developer/Ascend/cann-9.1.0`）。
- **适用粒度**：`operator_family`（所有使用 npu_op_library cmake 构建系统的 ACLNN 算子仓）。
- **路线优先级**：`safety_fallback`——优先尝试 `IMPL_OP_OPTILING.TilingParse`；当构建系统不触发 TilingParse 时回退到 `ctx_->GetPlatformInfo()` 直读平台信息。
- **不适用或未验证场景**：使用 ops-math build.sh（非 cmake npu_op_library）的算子仓可能正常触发 TilingParse，本卡的诊断与回退不适用；a2/a3 平台未验证。

## 判别方法

### 触发条件

smoke test 或 aclnn runtime 调用 `aclnxxxGetWorkspaceSize` 返回 561002（`ACLNN_ERR_INNER_TILING_ERROR`），且 tiling 函数已注册（`IMPL_OP_OPTILING.Tiling` 被调用）但返回非 SUCCESS，而 kernel binary 与构建均成功。

### 诊断探针

在 tiling 函数的 `GetShapeInfo`（或等价入口）中，对 `GetCompileInfo<T>()` 的返回值加 stderr 诊断输出；同时在 `TilingParse` 回调入口加一行 DBG 输出以确认它是否被调用：

```cpp
// tiling.cpp — GetShapeInfo 入口
const auto* compileInfo = ctx_->GetCompileInfo<SoftplusV2GradCompileInfo>();
fprintf(stderr, "[DBG] compileInfo=%p\n", (void*)compileInfo);

// tiling_entry.cpp — TilingParse 回调入口
static ge::graphStatus TilingPrepareForSoftplusV2Grad(gert::TilingParseContext* context) {
    fprintf(stderr, "[DBG] TilingPrepareForSoftplusV2Grad CALLED\n");
    // ...
}
```

重建后运行 smoke test，检查 stderr 输出与 build log：

```bash
cd operators && ./build.sh <pkg> > /tmp/build.log 2>&1
cd <pkg>/tests/aclnn && ./run.sh 2>/tmp/run.log
grep -E "\[DBG\]" /tmp/run.log /tmp/build.log
```

### 原始观测

- `[DBG] compileInfo=(nil)` 出现在 runtime log——CompileInfo 为 null。
- `[DBG] TilingPrepareForSoftplusV2Grad CALLED` **未出现**在 build log 和 runtime log——TilingParse 从未被调用。
- `IMPL_OP_OPTILING(...).Tiling()` 注册的 Tiling 函数**确实被调用**（GetShapeInfo 的 DBG 输出可见），但 `.TilingParse<>()` 注册的回调不生效。

### 解释

在 CANN 9.1.0 的 npu_op_library cmake 构建系统中，`IMPL_OP_OPTILING(OpType).TilingParse<T>()` 注册不触发 TilingParse 回调——无论在 build 期（kernel binary 生成）还是 runtime 期。因此 `GetCompileInfo<T>()` 返回 null。若 tiling 函数在 CompileInfo 缺失时直接 `return GRAPH_FAILED`，则 runtime 返回 561002。

根因链：`IMPL_OP_OPTILING.TilingParse` 未生效 → TilingPrepare 未执行 → CompileInfo 未写入 → `GetCompileInfo` 返回 null → tiling 函数 FAILED → 561002。该解释基于上述 DBG 探针的 tool_observed 观测，而非对 CANN 框架内部实现的源码级证实。

诊断后的处置方向：GetShapeInfo 不再硬依赖 CompileInfo，null 时回退到 `ctx_->GetPlatformInfo()` + `PlatformAscendC` 直读 `coreNum`/`ubSize`；UT 直接编译 tiling.cpp 时需为 PlatformAscendC 追加 `platform` 链接库。

## 验证信号

- smoke test 修复前全部返回 561002 失败，修复后 3/3 PASSED（exit 0）（来源平台:950；证据等级:tool_observed）
- TilingUT 30/30 pass、无回归（来源平台:950；证据等级:tool_observed）
- TilingPrepareForSoftplusV2Grad 在 npu_op_library 构建系统中 build 期和 runtime 期均未被调用（DBG fprintf 确认，日志无 `[DBG] TilingPrepareForSoftplusV2Grad CALLED`）（来源平台:950；证据等级:tool_observed）
- GetCompileInfo 返回 null（DBG fprintf 确认 `compileInfo=(nil)`）（来源平台:950；证据等级:tool_observed）

## 失效边界

- a2/a3 平台未验证；`GetPlatformInfo` + `PlatformAscendC` 是通用 CANN API，理论上可迁移，但未实测。
- ops-math build.sh 构建系统可能正常触发 TilingParse，此时不需要 GetPlatformInfo 回退；本卡的诊断结论仅对 npu_op_library cmake 构建系统成立。
- 若 tiling 函数确实需要 CompileInfo 中只有 TilingParse 才能写入的算子级编译常量（而非仅 coreNum/ubSize），GetPlatformInfo 回退无法覆盖该信息，需另行解决 TilingParse 注册问题。

## 预防

- 在 tiling 函数中，CompileInfo 的使用应始终 null-check + fallback，不要假设 TilingParse 已运行。
- 将 TilingParse 注册与公共 tiling 逻辑分文件：entry.cpp 注册（链接 opp_registry/platform），tiling.cpp 公共逻辑（UT 直接编译），避免 UT 引入传递链接依赖。
- smoke test 是检测 561002 的第一道防线：任何 tiling 注册方式变更后立即跑 `./run.sh`。

## 坏实践

- 在 GetShapeInfo 中直接 `if (compileInfo == nullptr) return GRAPH_FAILED;` 而不提供 fallback——在 TilingParse 未触发的构建路径下直接导致 561002。
- 把 TilingParse 注册和公共 tiling 逻辑放在同一文件——UT 直接编译该文件时引入 opp_registry 等传递链接依赖，链式报错。

<!-- cannbot:related:start -->
## 相关

- [CompileInfo](../../apis/utils_api/tiling_tuning/context_builder/compile_info.md)（`exemplifies`）：CompileInfo 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：CompileInfo 只能在 BuildTilingContext 链中注入；ContextBuilder、Outputs 回退、TilingDebug 及两张空 CompileInfo 故障直接验证上下文排序约束。
- [ContextBuilder构造函数](../../apis/utils_api/tiling_tuning/context_builder/context_builder_constructor.md)（`exemplifies`）：ContextBuilder构造函数 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：ContextBuilder 构造后链式设置算子名、I/O、属性、平台与实例数，再 BuildTiling/KernelContext；调测和 CompileInfo 故障验证该独立上下文链。
- [SetTiling（OpAICoreDef）](../../apis/utils_api/prototype_register_management/op_ai_core_def/set_tiling.md)（`exemplifies`）：SetTiling（OpAICoreDef） 与《561002：TilingParse 未生效，CompileInfo 为空》的实质衔接是：SetTiling 作用于 OpAICoreDef 的 tiling 对象，TilingParse 空与 ValueDepend 轴错误是 host tiling 注册阶段的直接失败模式。
- [Tiling调测](../../apis/utils_api/tiling_tuning/tiling_tuning.md)（`exemplifies`）：该 runbook 展示离线/运行链中 TilingParse 未生效导致 CompileInfo 为空和 561002，可作为 ContextBuilder 输入完整性的失败信号。
- [标量输入被赋非标量 shape 致 561002 判别](shape_561002.md)（`related`）：shape_561002 是同错误码但根因在输入 shape；与本卡的 compileInfo 空指针对照可按 TilingParse 日志先分流。
- [te_fusion 未调 TilingPrepare 致 GEIR FPE](te_fusion_tilingprepare_geir_fpe.md)（`same_topic`）：“te_fusion 未调 TilingPrepare 致 GEIR FPE”定义：GEIR 图测试全 case 返回 GE error 4294967295 并抛 Python FPE；根因是 GE te_fusion/build_single_op 编译子路径不调 TilingParse<TilingPrepare> 填 compileInfo，tiling 函数读 compileInfo=0 除零。用 fprintf 探针判别三条 run 路径的 TilingPrepare 调用语义。；“561002：TilingParse 未生效，CompileInfo 为空”定义：在 npu_op_library（cmake）构建系统中 IMPL_OP_OPTILING.TilingParse 注册不触发回调，runtime GetCompileInfo 返回 null 致 561002；诊断后回退 GetPlatformInfo 直读平台信息。。实质衔接：两卡都定位 TilingParse/TilingPrepare 未填 CompileInfo；ContextBuilder 的平台与 CompileInfo 注入接口用于构造可执行探针和避免除零。
<!-- cannbot:related:end -->
