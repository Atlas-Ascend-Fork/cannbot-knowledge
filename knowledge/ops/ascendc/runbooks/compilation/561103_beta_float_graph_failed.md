---
type: "Runbook"
title: "561103: beta 属性按 float 读致 GRAPH_FAILED"
description: "softplus_v2_grad 的 Host TilingFunc 用 float 指针读 double 存储的 beta 属性，把 8 字节 double 按 4 字节 float 重解释得到 0.0，CheckBetaRange 失败返回 GRAPH_FAILED，aclnn GetWorkspaceSize 报 561103 ACLNN_ERR_INNER_NULLPTR；判据为 fprintf 探针观测 beta=0.000000，正解按 L0 API 声明类型 double 读再 static_cast<float>。"
tags: ["task.debugging", "topic.tiling", "topic.precision"]
status: stable
sources: []
created_at: "2026-08-18T07:49:36Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 561103: beta 属性按 float 读致 GRAPH_FAILED

## 适用场景

- **工程形态**：aclnn 算子仓开发（ops-registry-invoke），Host TilingFunc（`op_host/arch35/*_tiling_arch35.cpp`）读取 gert::TilingContext 属性。
- **API 路径**：`attrs->GetAttrPointer<T>(idx)` / `OP_CHECK_NULL_WITH_CONTEXT`；L0 op_api `l0op::SoftplusV2Grad(gradOutputContiguous, selfContiguous, beta, threshold, ...)`；错误码 561103（`ACLNN_ERR_INNER_NULLPTR`）。
- **验证平台与版本**：Ascend950（dav-3510），CANN 9.1.0；aclnn ST 冒烟 12/12 通过。
- **适用粒度**：`same_operator`（softplus_v2_grad 的 Host 属性读取；机制对"L0 API 以 double 传标量属性"的同类算子同样适用）。
- **路线优先级**：`recommended_fastpath`（按属性在 L0 API 的声明类型读，是正解）。
- **不适用/未验证场景**：属性本就以 float 在 L0 API 声明的算子不适用；a2/a3 平台未验证，推断可迁移。

## 判别方法

**触发**（tool_observed 失败）：在 Ascend950（CANN 9.1.0，SoC dav-3510）上为 softplus_v2_grad 跑 Branch-4 aclnn ST 冒烟（`operators/softplus_v2_grad_package/tests/aclnn && bash run.sh`）。`./build.sh softplus_v2_grad_package` 编译通过，但 `bash run.sh` 跑用例时 aclnn `GetWorkspaceSize` 返回 **561103**（`ACLNN_ERR_INNER_NULLPTR`）。aclnn op_api 侧 `l0op::SoftplusV2Grad(...)` 返回 nullptr，触发 `CHECK_RET(... != nullptr, ACLNN_ERR_INNER_NULLPTR)`。当时 kernel 与 TilingFunc 已从桩切到真实实现，TilingFunc 里读 `beta` 属性并做 `beta > 0` 校验（`CheckBetaRange`，对应 spec `machine_constraint.float_in_range.lower_exclusive = 0`）。

**探针**（可执行检查）：在 `TilingFunc<Op>` 里临时加 `fprintf(stderr, "DEBUG beta=%f dtGradOut=%d dtSelf=%d\n", beta, (int)dtGradOut, (int)dtSelf);`（同步加 `#include <cstdio>`），重编 `./build.sh <pkg>`，重跑 `run.sh`，捕获 stderr。

**观测**（tool_observed）：`DEBUG beta=0.000000 dtGradOut=27 dtSelf=27`（27=DT_BF16 正确），`beta` 被读成 0.0 而非传入的 1.0/2.0；随后 `CheckBetaRange(beta>0)` 失败 → `kAttributeOutOfRange` → `return ge::GRAPH_FAILED`。

**判读**（根因解读）：softplus_v2_grad 的 L0 API 声明是 `double beta, double threshold`（标量属性在框架内按 `double` 存储）。TilingFunc 原先用 `float` 指针读该属性（`attrs->GetAttrPointer<float>(0)` 或等价写法），把 8 字节 double 的内存按 4 字节 float 重新解释，得到 0.0；`beta=0.0` 使 `beta > 0` 校验失败 → `GRAPH_FAILED` → `l0op::SoftplusV2Grad` 返回 nullptr → aclnn 561103。关键判据二联：fprintf 探针观测到 `beta=0.000000`（非传入值）；改按 `double` 读后 beta 恢复为 1.0/2.0 且 12/12 冒烟通过。注意 561103 是"框架级 nullptr"的笼统码，同一码在本 trace 还由另一根因触发（广播张量存储秩不匹配 → `l0op::Contiguous` 返回 nullptr，见 `561103_checkbroadcastshape`），须用探针区分到 TilingFunc 内部哪一步返回 GRAPH_FAILED。

## 验证信号

来源：softplus_v2_grad aclnn ST 冒烟（Ascend950，CANN 9.1.0）。修复前 561103 + fprintf 观测 beta=0.000000；改 `GetAttrPointer<double>` + `static_cast<float>` 并移除调试输出后重编重跑。

- 12/12 aclnn 冒烟用例通过（来源平台:950；证据等级:tool_observed）
- 561103 不再出现（来源平台:950；证据等级:tool_observed）
- 调试期 fprintf 观测 `beta=0.000000`（来源平台:950；证据等级:tool_observed）