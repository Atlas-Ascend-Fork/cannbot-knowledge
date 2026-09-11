---
type: Runbook
title: TileLang 算子紧耦合源码编译的 tilelang-ascend 框架：版本/分支错配 → codegen / aicore 报错
description: 用 TileLang 写的算子（SFA / lightning_indexer 等 DSA 稀疏注意力链路算子）在 bringup 时报错，而同目录别的 tilelang 算子却能跑通。这类算子用外部 tilelang-ascend 的 TIR DSL（T.copy / T.fill / T.gemm_v0 / T.barrier_all 等）编写，该框架非 pip 预装、须从上游源码编译安装（git clone --recursive + bash install_ascend.sh），且用的是特定 fork/分支（ascendc_pto / pto），属活跃演进的实验性框架——排障方向应先判「框架 vs 仓内核定义的版本/分支是否匹配」，而不是先怀疑自己的建模脚本 / config / 核算子逻辑。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/47
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/52
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/141
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a2
---

# TileLang 算子紧耦合源码编译的 tilelang-ascend 框架：版本/分支错配 → codegen / aicore 报错

## 适用场景

用 [TileLang](../../concepts/frameworks/tilelang.md) 写的算子（[SFA](../../concepts/kernels/sparse_flash_attention.md) / [lightning_indexer](../../concepts/kernels/lightning_indexer.md) 等 [DSA](../../concepts/modules/dsa.md) 稀疏注意力链路算子）在 bringup 时报错，而**同目录别的 tilelang 算子却能跑通**。这类算子用外部 `tilelang-ascend` 的 TIR DSL（`T.copy` / `T.fill` / `T.gemm_v0` / `T.barrier_all` 等）编写，该框架**非 pip 预装、须从上游源码编译安装**（`git clone --recursive` + `bash install_ascend.sh`），且用的是特定 fork/分支（`ascendc_pto` / pto），属活跃演进的实验性框架——排障方向应**先判「框架 vs 仓内核定义的版本/分支是否匹配」，而不是先怀疑自己的建模脚本 / config / 核算子逻辑**。

## 信号（三种表现，同一根源）

- **缺原语**：`module 'tilelang.language' has no attribute 'fill'`（parse 阶段，冒泡为 `tvm.error.DiagnosticError`）。核定义调 `T.fill(acc_o, 0.0)`，但装的 TileLang 无 `fill` 属性。
- **原语签名漂移**：`TypeError: npu_copy_v2() got an unexpected keyword argument 'srcN'`（codegen 阶段，栈落在 TVMScript 求值器 `_eval_expr` 内）。旧核定义生成的 `npu_copy_v2(...)` 调用带 `srcN` 关键字，而当前框架的 `npu_copy_v2` 已不接受它。
- **动态 shape aicore error**：动态 shape 下算子报 "aicore error"（NPU 侧症状），但根因在 host 侧——JIT 的 cython kernel wrapper 把动态维度当**裸 Python int** 直接传，未显式转 `ctypes.c_int64`，x86 host 按错误位宽把 dim 传给 native kernel launch。

## 触发条件 + 根因

三者都是「仓内 tilelang 核定义 ↔ 外部 tilelang-ascend 框架」的版本/分支错配，只是错配落点不同：

- **分支错配**：按仓 README 自装指令 clone 的是 tilelang-ascend **默认分支**（README 未 pin `ascendc_pto`），装出的 TileLang 缺 `ascendc_pto` 分支特有的原语（如 `tilelang.language.fill`），parse 到该原语即 `AttributeError`。
- **原语签名漂移**：框架侧 DSL 原语（`T.copy` → `npu_copy_v2`）的形参随版本演进变了，而仓内核定义仍按旧签名生成调用 → codegen 报 `unexpected keyword argument`。这不是核算子逻辑 bug，也非硬件/抢卡问题。
- **框架后端 bug**：框架的 cython kernel wrapper 在动态维度传参上有整型位宽缺陷（裸 int append → 应 `ctypes.c_int64(...)` 包裹）。该传参路径是**所有 tilelang JIT kernel 公用**的、非某算子专属，"aicore error" 掩盖了一个 host 侧 x86 整型传参 bug。

## 修法

- **首选：别自装、用钉好的环境**——用仓 README 提供的**预装 docker 镜像**（TileLang 代码仓及依赖已全部预装、分支已 pin），或 **pin 维护者指定的 `ascendc_pto` 分支**（`tilelang-ascend/tree/ascendc_pto/...`），不要 clone 默认/任意分支自装。
- **框架 API 漂移 / 后端 bug：两侧同步、缺一不可**——把 tilelang-ascend **更新到含修复的版本并重新源码编译安装**（源码构建，非增量替换单文件），同时**更新仓内算子定义 + 用例**使其与新框架的原语签名对齐。
- **诊断先验（可迁移核心）**：tilelang-backed kernel 在 codegen 报 `has no attribute '<原语>'` / `unexpected keyword argument`，或动态 shape 下报 aicore error 时——优先核对/升级 tilelang-ascend 框架、怀疑 JIT 的 host 侧参数下发路径，**而不是先改建模脚本**。`has no attribute` / `unexpected keyword argument` 即「装的 TileLang 分支/版本与仓算子源不匹配」的失败签名。

## 适用边界

限 tilelang-backed kernel（DSA 稀疏注意力算子等），不外推为全栈通用律。tilelang-ascend 是实验性、活跃演进、源码编译的框架，这类分支/签名漂移是使用它的**固有风险**——引用时以目标 recipe 当时 pin 的镜像/分支为准。仓内 `ops/tilelang` 目录经历过重组（旧根路径算子已挪到 `ds_v32/` / `ds_v4/` 子目录），但同一分支/版本错配陷阱在新布局仍可复现。

## Evidence

- **缺原语 · diff 事实**（clone `@8dd3a3b`）：`sparse_flash_attention.py` 多处 `T.fill(...)`（197/198/199/216 行）、`lightning_indexer.py` 亦用 `T.fill`，与 traceback 逐行对上；README §2 自装 clone 默认分支、全文无 `ascendc_pto`。**维护者确认**指向 `ascendc_pto` 分支 + 预装镜像。「哪个分支含 `fill`」为据维护者指引 + 报错的推断、未独立核两分支源码。
  - 溯源下探：[cann-recipes-infer-issue-141-question-https-gitcode-com-cann-cann-recipes-infer-blob-master-ops-tilel](https://gitcode.com/cann/cann-recipes-infer/issues/141)
- **原语签名漂移 · 维护者确认 + diff 事实**（clone `@363df3e`）：两名维护者确认根因为 tilelang-ascend 框架变更、给修法（更新框架重编 + 更新仓内 indexer 定义/用例）；修后 `T.copy(C_L0, QK_RES[...], enable_relu=True)` 已不再产生 `srcN` 关键字。
  - 溯源下探：[cann-recipes-infer-issue-47-bug-report-tilelang-example-test-lightning-indexer-py](https://gitcode.com/cann/cann-recipes-infer/issues/47)
- **框架后端 bug · diff 事实 + 维护者确认**（tilelang-ascend `@ba306cb` "Fix dynamic shape on x86"）：单文件 `cython_wrapper.pyx` 的 `CythonKernelWrapper` 把动态 dim 由裸 append 改为 `ctypes.c_int64(...)` 包裹；维护者已复现并确认更新到含该修复的框架即修复。原始 aicore error 仅以截图给出、未 OCR，症状→根因映射依赖维护者定位 + 该 PR 确为动态 shape/x86 修复。
  - 溯源下探：[cann-recipes-infer-issue-52-bug-report-shape-sfa-aicore-error](https://gitcode.com/cann/cann-recipes-infer/issues/52)