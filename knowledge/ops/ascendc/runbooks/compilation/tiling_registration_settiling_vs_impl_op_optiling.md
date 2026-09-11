---
type: "Runbook"
title: OpDef SetTiling 与 IMPL_OP_OPTILING 二选一
description: host 侧 tiling 注册双通道等价：样例 IMPL_OP_OPTILING 与契约 OpDef .SetTiling 二选一，并存有双重注册风险；SetTiling 跨文件绑定实测通过。
tags: [task.implementation, topic.tiling]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# OpDef SetTiling 与 IMPL_OP_OPTILING 二选一


## 现象

把算子仓样例工程改写为新算子的接口桩时，host 侧 tiling 注册遇到**双通道冲突**：样例工程（及其姊妹样例）的 tiling 注册走 `op_host/arch35/*_tiling_arch35.cpp` 文件末尾的宏注册器：

```cpp
IMPL_OP_OPTILING(AddCustom).Tiling(TilingFunc);
```

样例文件注释原文明说："This replaces the old-style .SetTiling() binding inside the OpDef class. The IMPL macro is the new CANN convention."——即样例的 OpDef（`op_host/*_def.cpp`）里**没有** tiling 绑定，改由 IMPL 宏注册。

而新算子的契约文档（算子原型 proto.md，OpDef 骨架必须与其逐项一致）给出的 OpDef 构造函数结尾是：

```cpp
this->AICore().SetTiling(optiling::TilingFunc).AddConfig("ascend950");
```

两条通道注册的是**同一个 tiling 回调**。改写时若 OpDef 里写 `.SetTiling(...)`、同时又原样保留 arch35 文件里的 `IMPL_OP_OPTILING(...)`，同一算子的 tiling 函数会被注册两次。正确做法是二选一：按契约走 OpDef `.SetTiling()` 通道，**删掉** arch35 文件里的 `IMPL_OP_OPTILING` 行，TilingFunc 的定义留在原文件，OpDef 侧用前置声明 + include 头文件做跨文件绑定。改写后构建一次通过，tiling 链路实测可用。InferShape/InferDataType 同理存在 `SetInferShape`/`SetInferDataType`（OpDef 内绑定）与 `IMPL_OP_INFERSHAPE`/`IMPL_OP`（文件级宏）两套通道，处理方式相同。

## 适用场景

- 工程形态：算子仓（ops-registry-invoke 流程）`op_host/` 侧 OpDef 与 tiling 改写——样例工程换算子名、OpDef 按契约重写时。
- API 路径：`register/op_def_registry.h` 的 `OpDef::AICore().SetTiling(fn)` / `SetInferShape(fn)` / `SetInferDataType(fn)`；文件级宏 `IMPL_OP_OPTILING(<OpType>).Tiling(fn)`；`exe_graph/runtime/tiling_context.h` 的 `gert::TilingContext`。
- 验证过的平台与 CANN 版本：950（ascend950/arch35）+ CANN 9.0.0-beta.2。
- 适用粒度：operator_family——所有从样例工程改写 OpDef/tiling 的自定义算子。
- 路线优先级：recommended_fastpath（契约要求 OpDef 绑定时：SetTiling 通道 + 删 IMPL 行 + 跨文件前置声明绑定）。
- 明确不适用 / 未验证：契约不约束注册通道时，纯样例式 IMPL 宏注册同样可用（本 trace 未单独实测该通道）；双通道并存的失败形态未实测；`IMPL_OP_INFERSHAPE` 通道未实测。

## 根因

host 侧 tiling 函数有两条**等价**的注册通道——OpDef 构造内 `.AICore().SetTiling(fn)`（经典 API：把函数指针存进 OpDef 注册项）与文件级静态注册器宏 `IMPL_OP_OPTILING(<OpType>).Tiling(fn)`（样例注释称的"新约定"）；两者向框架注册的是同一个回调，改写样例时如果契约要求 OpDef 内绑定而样例残留 IMPL 宏行，就构成同一回调的双重注册。

## 解决配方

**before**——样例形态：OpDef 无 tiling 绑定 + arch35 文件末尾宏注册（两处verbatim）：

```cpp
// op_host/arch35/add_custom_tiling_arch35.cpp 文件末尾（样例原文，含注释）
// =============================================================================
// IMPL_OP_OPTILING(AddCustom) — register tiling function with CANN
//
// .Tiling(TilingFunc):
//   Registers the runtime tiling function for AddCustom.
//   The framework invokes TilingFunc before every kernel launch to compute
//   block/tile partitioning (via AddCustomTilingData).
//
// This replaces the old-style .SetTiling() binding inside the OpDef class.
// The IMPL macro is the new CANN convention, matching scale_custom_package.
// =============================================================================
IMPL_OP_OPTILING(AddCustom).Tiling(TilingFunc);
```

**after**——契约形态：OpDef 内 `SetTiling` 绑定 + arch35 文件只留 TilingFunc 定义（无注册行）。OpDef 文件（`op_host/<op>_def.cpp`，verbatim 取自当次终版写入）：

```cpp
#include "arch35/thnn_fused_gru_cell_grad_tiling_arch35.h"
#include "register/op_def_registry.h"

namespace ge {
// InferShape / InferDataType 桩的前置声明（定义见上方注释所列文件），
// 供 OpDef 的 SetInferShape / SetInferDataType 绑定函数指针。
graphStatus InferShape(gert::InferShapeContext* context);
graphStatus InferDataType(gert::InferDataTypeContext* context);
} // namespace ge

namespace ops {

// OpDef 原型与算子原型文档 §1 逐项一致：
// Input/Output/Attr 的名称、顺序、ParamType、DataType、Format 组合均不变。
class ThnnFusedGruCellGrad : public OpDef {
public:
    explicit ThnnFusedGruCellGrad(const char* name) : OpDef(name)
    {
        this->Input("grad_hy").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Input("storage").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("grad_input_gates").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("grad_hidden_gates").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("grad_hx").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("grad_input_bias").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Output("grad_hidden_bias").ParamType(REQUIRED)
            .DataType({ge::DT_FLOAT, ge::DT_FLOAT16, ge::DT_BF16})
            .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
        this->Attr("has_bias").AttrType(OPTIONAL).Bool(false);
        this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);
        this->AICore().SetTiling(optiling::TilingFunc).AddConfig("ascend950");
    }
};

OP_ADD(ThnnFusedGruCellGrad);

} // namespace ops
```

配套声明头（`op_host/arch35/<op>_tiling_arch35.h`，TilingFunc 定义留在 arch35 .cpp、不搬进 def.cpp）：

```cpp
#ifndef THNN_FUSED_GRU_CELL_GRAD_TILING_ARCH35_H
#define THNN_FUSED_GRU_CELL_GRAD_TILING_ARCH35_H

#include "exe_graph/runtime/tiling_context.h"

namespace optiling {

// TilingFunc 桩：仅保证 tiling 通路可用（1 核 / 无 workspace / 写占位字段）；
// 真实分核/切分算法真实分核/切分算法由 tiling-developer 按 design/HostTiling.md 落地。
ge::graphStatus TilingFunc(gert::TilingContext* context);

} // namespace optiling

#endif // THNN_FUSED_GRU_CELL_GRAD_TILING_ARCH35_H
```

改写要点清单：

1. OpDef 构造内补 `.AICore().SetTiling(optiling::TilingFunc).AddConfig("ascend950")`（按契约）；
2. **删除** arch35 tiling 文件末尾的 `IMPL_OP_OPTILING(<OpType>).Tiling(TilingFunc);` 行；
3. def.cpp `#include "arch35/<op>_tiling_arch35.h"` 拿到 TilingFunc 声明（quote 包含按 def.cpp 所在目录相对解析到 `op_host/arch35/`）；
4. InferShape/InferDataType 若契约也要求 OpDef 绑定：def.cpp 里前置声明（`namespace ge` 内 `graphStatus InferShape(gert::InferShapeContext*)` 等），定义留在各自文件，同样删除对应的 `IMPL_OP_INFERSHAPE`/`IMPL_OP` 注册行。

## 设计决策

- **为何走 SetTiling 通道**：算子契约（proto.md）是 OpDef 骨架的唯一事实源，其 §1 明确 `AICore().SetTiling(...)`；经典 API 在 CANN 各版本持续支持。TilingFunc 定义留在 arch35 文件、CMake 的 host 源 glob 不用动。
- **为何删 IMPL 行而不是两处都留**：两通道等价注册同一回调，并存 = 双重注册（失败形态未实测，按风险规避）。
- **跨文件绑定为何安全**：`SetTiling`/`SetInferShape` 只是存函数指针，不依赖跨编译单元静态初始化顺序；定义与声明经 include 对齐签名（`ge::graphStatus (*)(gert::TilingContext*)`）即可，最终链接进同一个 host 库（`libascend_all_ops.so`）。
- **放弃的候选**：纯样例式 IMPL 宏注册（偏离契约，弃）；InferShape/InferDataType 全部内联进 def.cpp 做 static 函数（recipe 式单文件写法，弃——会空置样例已有的 infershape/graph_infer 文件与 CMake glob）。
- 当前方案属 recommended_fastpath（契约约束下的最低风险转换）。

## 系统信息

- CANN 9.0.0-beta.2 / ascend950（arch35 模板）。
- 相关文件：`op_host/<op>_def.cpp`（OpDef + OP_ADD）、`op_host/arch35/<op>_tiling_arch35.{h,cpp}`（TilingFunc 声明/定义）、`op_host/<op>_infershape.cpp`（InferShape 定义）、`op_graph/<op>_graph_infer.cpp`（InferDataType 定义）、顶层 `CMakeLists.txt`（`host_tiling_srcs`/`host_graph_srcs` glob 这三个源文件）。
- 构建命令：`cd operators && ./build.sh <Pkg>_package`。

## 完整代码

见「解决配方」——before（样例 IMPL 注册行）与 after（OpDef 全文 + 声明头 + 改写要点清单）均为 verbatim 函数/文件级代码块。

## 预防

- 从样例改写 OpDef 前，先读契约对注册通道的要求；契约给的是 OpDef 内绑定（SetTiling/SetInferShape）时，把"删除样例的 IMPL_OP_* 注册行"列入改写清单。
- 全文 grep `IMPL_OP_OPTILING|IMPL_OP_INFERSHAPE|IMPL_OP(` 确认无残留注册行再构建。

## 验证信号

以下信号来自同一次"样例重建为接口桩"会话：SetTiling 通道 + 跨文件前置声明绑定改写完成后，构建安装与 aclnn 冒烟一次通过。

- 构建一次通过：`BUILD_EXIT=0`（cmake + make binary package + CPack `.run` 安装 SUCCESS）（来源平台：950；证据等级：tool_observed）。
- 构建日志无 `do not registe tiling struct` 告警（来源平台：950；证据等级：tool_observed）。
- aclnn 两段式冒烟（`GetWorkspaceSize` → launch → sync）fp32/fp16/bf16 3/3 PASSED——`GetWorkspaceSize` 阶段会执行 tiling 回调，SetTiling 绑定的 TilingFunc 在 aclnn 通路被实际调用且返回成功（来源平台：950；证据等级：tool_observed）。
- 已安装 3 个 `.o`（= DataType 组合数）且 mocker 串计数均为 1（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 双通道并存（SetTiling + IMPL_OP_OPTILING 同时保留）的实际失败形态（编译错/链接错/运行断言/静默覆盖）未实测——本卡按"等价通道二选一"规避，不声称具体失败模式。
- 纯 IMPL 宏通道（不动 OpDef）在本 trace 未跑通验证（仅样例在用）；契约不约束时不应默认它有问题。
- InferShape/InferDataType 桩只验证了编译通过与链接；aclnn 直调通路是否实际触发图推理未单独验证。
- 其他 CANN 版本的宏/API 形态未验证（推断可迁移，未验证）。

## 坏实践

- 改写时"两处都留"——OpDef 写 SetTiling 又保留 IMPL 注册行，赌框架去重（未实测的冒险）。
- 机械 sed 改名后不看注册通道语义，直接构建——样例与契约的通道差异会被改名操作完整继承下来。

## 误诊

- 曾把样例的 IMPL 宏通道当作"必须保留的新约定"而犹豫是否照抄——样例注释只是说明该样例版本的写法偏好，契约才是改写时的仲裁源；两通道等价（样例注释 + agent 分析，未实测对照）。

## 未决事项

- 优先项：实测双通道并存的失败形态（构建期报错还是运行期冲突），把"双重注册风险"从推断变成结论。
- IMPL 宏通道与 SetTiling 通道在 aclnn 运行期的等价性可做一次对照实验（同算子两种通道各构建一次）。
