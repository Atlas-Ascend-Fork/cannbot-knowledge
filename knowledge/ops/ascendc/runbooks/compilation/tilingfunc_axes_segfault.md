---
type: "Runbook"
title: "TilingFunc 未声明依赖读 axes 致 segfault"
description: "vendor TilingFunc 内对 axes 输入(index 1) 调 GetInputTensor(1)->GetData<int32_t>() 而 未声明 TilingInputsDataDependency({1}) 时，C++ ST aclnn segfault；回退该读取即恢复。该读法在未声明依赖时禁用。"
tags: ["task.debugging", "topic.implementation.tiling"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
aliases: ["EuclideanNorm"]
---

# TilingFunc 未声明依赖读 axes 致 segfault

## 现象

在 Ascend950PR（soc=ascend950，CANN 9.0.0-beta.2）调试 `euclidean_norm` 归约算子时，为了让 vendor `TilingFunc` 能按 axes 的**实际值**（而非 axes 的 COUNT）划分 reduce 轴，agent 在 `op_host/arch35/euclidean_norm_tiling_arch35.cpp` 的 `LoadAxesValues` 路径里对 axes 输入（`GetInputTensor(1)`）取 `GetData<int32_t>()` 读取轴值，且**未**在 `IMPL_OP_OPTILING(...).Tiling(TilingFunc)` 注册链上声明 `.TilingInputsDataDependency({1})`（因同名 built-in `InputsDependency` 冲突，声明它会在 TTK 重现 attr 越界，本 trace 另行记录该 built-in 冲突）。

改完跑 C++ ST（`tests/aclnn/run.sh`）：进程 **segfault**（段错误）。把 `InferShape` 改回安全版本后仍 segfault——定位到 segfault 源在 `TilingFunc` 的 `LoadAxesValues`：未声明 data dependency 时 `GetInputTensor(1)` 返回的 Tensor 不持有 host 端可读内存，`GetData<int32_t>()` 解引用即崩。回退 `op_host/arch35/euclidean_norm_tiling_arch35.cpp`（`git checkout`）后 C++ ST 恢复至 baseline 通过率（82 PASS / 15 FAIL，与改动前一致）。

## 适用场景

- **工程形态**：ops-registry-invoke vendor 算子仓，Host Tiling 阶段需读 axes 等数据相关输入的值。
- **API 路径**：`TilingContext::GetInputTensor(index)` → `Tensor::GetData<T>()`；`.TilingInputsDataDependency({idx,...})` 注册。
- **验证平台与版本**：Ascend950PR（soc=ascend950），CANN 9.0.0-beta.2。仅 950 实测。
- **适用粒度**：`operator_family`（任何 vendor TilingFunc 试图在 tiling 期读 axes/动态输入数据的归约/动态 shape 算子）。
- **路线优先级**：`banned`——在未声明 `TilingInputsDataDependency` 的情况下直接 `GetInputTensor(i)->GetData<T>()` 是禁用路线；要么先声明依赖、要么不读数据改走 shape/count 路径。
- **不适用/未验证场景**：a2/a3 未验证。本卡只覆盖 "未声明依赖 → 解引用即崩" 这一负路径；声明依赖后能否正常取数据在本 trace 因 built-in 冲突未能验证。

## 失败路线

**尝试**：在 vendor `TilingFunc` 的 `LoadAxesValues` 路径里对 axes 输入（index 1）调用 `GetInputTensor(1)->GetData<int32_t>()` 读取轴值，期望在 tiling 期按 axes 实际值划分 reduce 轴，而**不**在算子 tiling 注册上声明 `.TilingInputsDataDependency({1})`。

**失败 / 回退**：

1. 改完跑 C++ ST（`tests/aclnn/run.sh`）→ 进程 segfault（段错误，无输出）。
2. 先把 `InferShape` 改回安全版本隔离变量 → 仍 segfault，排除 `InferShape` 因素，segfault 源在 `TilingFunc` 的 `LoadAxesValues`。
3. `git checkout -- op_host/arch35/euclidean_norm_tiling_arch35.cpp` 回退该 TilingFunc 改动 → C++ ST 恢复至 baseline 通过率（82 PASS / 15 FAIL，与改动前一致），构成"该读取导致崩溃、移除即恢复"的闭环。

**边界（banned）**：在未声明 `TilingInputsDataDependency` 的情况下直接 `GetInputTensor(i)->GetData<T>()` 解引用数据是禁用路线。本 trace 的 950 / CANN 9.0.0-beta.2 环境下稳定 segfault。替代正路径有二：先声明 `.TilingInputsDataDependency({i})` 再读（本 trace 因 built-in 同名冲突未能验证），或不读数据改走 shape/count 路径。

## 根因

`TilingContext::GetInputTensor(index)` 的契约：仅当算子通过 `TilingInputsDataDependency({...})` 声明了对应输入为 tiling 数据依赖时，返回的 Tensor 才持有 host 端可读内存；否则该内存不可解引用。本 trace 实测在未声明依赖时 `GetInputTensor(1)` 的返回不持有可读内存，`GetData<int32_t>()` 解引用即 segfault。

agent 据 segfault 行为推断 `GetInputTensor(1)` 返回"非空但无效"指针（与 `tiling_context.h` 文档"反之返回 nullptr"的描述不一致），但该推断仅来自崩溃行为反推，未直接观测到指针值，属解释而非实测。

为何本算子不能声明依赖：vendor `euclidean_norm` 与 built-in `libophost_legacy.so` 同名，built-in 已注册 `InputsDependency`，vendor 的 `.TilingInputsDataDependency({1})` 被 "has been registered" 拒绝、且会触发 built-in data-dependency 路径访问 attr[1] 越界（本 trace 另行记录该 built-in 冲突）。于是在本环境下"声明依赖"与"不声明直接读"两条路都被堵死——前者触发框架越界，后者 segfault。

## 验证信号

本 trace 实测信号（均在 950 平台、CANN 9.0.0-beta.2）：

- C++ ST 在 `TilingFunc` 的 `LoadAxesValues` 路径（`GetInputTensor(1)->GetData<int32_t>()`、未声明 `TilingInputsDataDependency`）下 segfault；先把 `InferShape` 改安全后仍 segfault，定位 segfault 源在 `TilingFunc` 而非 `InferShape`。（来源平台:950；证据等级:tool_observed）
- 回退 `op_host/arch35/euclidean_norm_tiling_arch35.cpp`（`git checkout`）后，C++ ST 恢复至 baseline 通过率（82 PASS / 15 FAIL，与改动前一致），构成"该读取导致崩溃、移除即恢复"的闭环。（来源平台:950；证据等级:tool_observed）

## 失效边界

- 平台：仅 950 实测。a2/a3 未验证、未定位——不得据 950 结果推断其他平台 `GetInputTensor` 的返回契约。
- CANN 版本：9.0.0-beta.2。其他版本 `GetInputTensor` 在未声明依赖时的返回值（nullptr vs 非空无效）可能不同，需重测。
- 触发条件：仅当 vendor 算子名与 built-in 重名、无法声明 `TilingInputsDataDependency` 时，本"未声明依赖直接读"的负路径才会被尝试。非同名算子应走"声明依赖后读"的正路径（本 trace 未验证该正路径）。