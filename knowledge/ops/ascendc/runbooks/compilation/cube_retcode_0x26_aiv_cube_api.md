---
type: "Runbook"
title: "Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界"
description: "Cube 核直调 kernel 入口 extern \"C\" __global__ __aicore__ 未标记核类型时 bisheng 按 MIX 模式编译，kernel 被派发到 AIV 核执行 Cube 专属 API（LoadData/Mmad/Fixpipe），AIV 核无 L0A/L0B/L0C 硬件单元，访问 AIC 内部 buffer 越界，触发 aicore exception retCode=0x26 / ErrCode=507015，plog 表现为 aivector error 而非 Cube 侧错误。判别要点：代码用 Cube API、报错却是 aivector error + fixp_error 非零 + scalar access internal buffer of AICore is out of bounds。"
tags: ["task.debugging", "topic.programming_model.execution_unit.cube", "topic.implementation"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: '2026-08-27T12:23:11Z'
platforms: ["a3"]
---

# Cube 直调 retCode=0x26：AIV 误跑 Cube API 越界

## 现象

编写 rain_fusion_attention 算子 PV 相乘（BlockMmadPV）的 Cube 核直调验证原型：kernel 入口写为 `extern "C" __global__ __aicore__ void pv_matmul_verify_entry(...)`，函数体调用 Cube 专属 API（`AscendC::LoadData` / `AscendC::Mmad` / `AscendC::Fixpipe`），通过 `<<<1, nullptr, stream>>>` 在 A3 实体卡（ascend910_93 / dav-2201, CANN 9.1.0）上启动。Host 调 `aclrtSynchronizeStream` 同步流失败，plog（`/home/developer/ascend/log/debug/plog/plog-<pid>_<ts>.log`）原文报错：

```
[ERROR] RUNTIME ... [davinci_kernel_task.cc:1262] ... PreCheckTaskErr:An error occurred in the kernel task, retCode=0x26, [aicore exception].
[ERROR] RUNTIME ... [stream.cc:1713] ... GetError:Stream Synchronize failed, stream_id=47, retCode=0x26, [aicore exception].
[ERROR] RUNTIME ... [stream.cc:1716] ... GetError:AI Core kernel task execution failed, retCode=0x26.
[ERROR] RUNTIME ... [api_c_stream.cc:158] ... rtStreamSynchronize:ErrCode=507015, desc=[aicore exception], InnerCode=0x7150026
[ERROR] RUNTIME ... [device_error_core_proc.cc:1118] ... PrintCoreInfo:The error from device(chipId:2, dieId:0) ... there is an exception of fftsplus aivector error, core id is 43 ... aic error mask: 0x6500020bd00028c ...
The extend info: errcode:(0, 0x200000000000000, 0) errorStr: The address for the scalar to access the internal buffer of AICore is out of bounds. fixp_error0 info: 0x1084ae3, fixp_error1 info: 0x13 ...
[ERROR] RUNTIME ... [davinci_kernel_task.cc:1210] ... [DFX_INFO]AI Core kernel execution failed ... fault kernel_name=pv_matmul_verify_entry ...
```

关键信号：`retCode=0x26 [aicore exception]`、`ErrCode=507015`、`aivector error`、`fixp_error` 非零、`errorStr: The address for the scalar to access the internal buffer of AICore is out of bounds`、故障 kernel 名为 `pv_matmul_verify_entry`。表面矛盾点：代码用的是 Cube 核 API，报的却是 **aivector error**（Vector 核侧异常）。

## 适用场景

- **工程形态**：AscendC Cube 核直调原型（`__global__ __aicore__` 入口 + `<<<>>>` 启动，非算子工程 / 非 aclnn）。
- **API 路径**：Cube 核 API（`DataCopy` Nd2Nz、`LoadData`/`LoadData2DParams`、`Mmad`/`MmadParams`、`Fixpipe`/`FixpipeParamsV220`），操作 L1/L0A/L0B/L0C Buffer。
- **验证过的平台与 CANN 版本**：A3 实体卡（ascend910_93 / `--npu-arch=dav-2201`），CANN 9.1.0。与 frontmatter `platforms: [a3]` 严格一致。
- **适用粒度**：`operator_family`（所有 Cube 核直调 kernel 入口均适用，不限 PV matmul）。
- **不适用或未验证场景**：算子工程（msOpGen / aclnn）方式由 op_host 侧控制核类型，不在本卡范围；Ascend950（950）仿真器见独立卡（cannsim 不支持 Cube 核直调）；A2（dav-200）未验证。

## 判别方法

**触发条件**：Cube 核直调 kernel（入口 `__global__ __aicore__`、函数体调 `LoadData`/`Mmad`/`Fixpipe` 等 Cube 专属 API）经 `<<<>>>` 启动后，`aclrtSynchronizeStream` 同步失败，plog 出现 `retCode=0x26 [aicore exception]` / `ErrCode=507015`，且故障定位为 `aivector error`（Vector 核侧）而非 Cube 核侧、`fixp_error` 非零、`errorStr` 指向 "The address for the scalar to access the internal buffer of AICore is out of bounds"。

**可执行探针**：
1. 在 kernel 入口函数体首行加运行时守卫 `if (g_coreType == AIV) { return; }`（参照官方 `cube_matmul_loaddata_operator` 示例），重新编译运行；若 `retCode=0x26` / `aivector error` 消失且 kernel 正常执行，即证实根因为 MIX 派发到 AIV 核。
2. 或在入口首行改用编译期宏 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY);`，bisheng 据此将 kernel 标为纯 Cube 核、不派发到 AIV；若异常消除则同样证实。
3. 检查 bisheng 编译输出是否含 "kernel 类型未标记" 类警告——该警告是 MIX 派发的前置信号，出现即高度吻合本判别。
4. 反向排除：`FixpipeParamsV220.srcStride`、`LoadData` 的 `srcStride` 取值下溢是独立的小问题，单独修这些不会消除 `retCode=0x26` 崩溃；若仅改 Fixpipe 参数崩溃依旧，应转向核类型派发排查。

**原始观测**（A3 实体卡，CANN 9.1.0，PV matmul 直调原型）：
- plog：`PreCheckTaskErr ... retCode=0x26 [aicore exception]`、`rtStreamSynchronize:ErrCode=507015`、`there is an exception of fftsplus aivector error, core id is 43`、`errorStr: The address for the scalar to access the internal buffer of AICore is out of bounds`、`fixp_error0 info: 0x1084ae3, fixp_error1 info: 0x13`、`fault kernel_name=pv_matmul_verify_entry`。
- 入口加 AIV 守卫（做法 A）后 `aivector error` 与 `retCode=0x26` 消失，kernel 完整执行。
- 改用 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY)`（做法 B）后同一 A3 卡上同样不再崩溃。

**机制解释**（根因，明确为分析结论）：bisheng 编译器对 `extern "C" __global__ __aicore__` 入口在**未显式标记 kernel 类型**（既无 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY)`，也无运行时 `g_coreType` 守卫）时，按 **MIX 模式**编译——kernel 同时被调度到 AIV（Vector）核与 AIC（Cube）核执行。Cube 专属 API（`LoadData`/`Mmad`/`Fixpipe`）操作的是 AIC 内部 buffer（L0A/L0B/L0C），AIV 核没有这些硬件单元，AIV 核执行这些 API 时访问 AIC 内部 buffer 越界 → `aivector error` → `aicore exception (retCode=0x26)`。这一机制链解释了"代码写的是 Cube API、报的却是 aivector error"的表面矛盾：错误来自被误派发的 AIV 核，而非 Cube 核自身参数错。修复方向是在入口标记核类型，确保 Cube 代码仅在 AIC 核执行。

## 验证信号

本次观测来自 rain_fusion_attention PV matmul Cube 核直调原型在 A3 实体卡上的开发会话。

- 修复前：`aclrtSynchronizeStream` 失败，plog `retCode=0x26 [aicore exception]`、`rtStreamSynchronize:ErrCode=507015`、`aivector error`、`errorStr: The address for the scalar to access the internal buffer of AICore is out of bounds`、`fixp_error` 非零、`fault kernel_name=pv_matmul_verify_entry`（来源平台：a3；证据等级: tool_observed）。
- 入口加 `if (g_coreType == AIV) { return; }` 守卫（做法 A）后，verify_result.py 输出 `Shape: [128,128], MaxDiff=0.007812, MeanDiff=0.000002, PassRatio=1.000000`、`RESULT: PASS`，`aivector error` 消失（来源平台：a3；证据等级: tool_observed）。
- 入口改用 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY)`（做法 B）后，同一 A3 卡上 `MaxDiff=0.007812, PassRatio=1.000000` 通过（来源平台：a3；证据等级: tool_observed）。

## 预防

- 写 Cube 核直调 kernel 入口时，**默认**在首行加 `KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIC_ONLY);`（编译期，官方推荐）；若无法改宏则加运行时 `if (g_coreType == AIV) { return; }` 守卫。
- 看到 plog 报 `aivector error` + `fixp_error` 非零 + `scalar access internal buffer of AICore is out of bounds` 而 kernel 用的是 Cube API 时，第一怀疑是 kernel 被 MIX 派发到 AIV 核执行，而非 Cube API 参数错。
- bisheng 对未标记类型的 `__aicore__` 入口会发 "kernel 类型未标记" 警告，不要忽略——该警告即本根因的前置信号。

## 坏实践

- 误把 `aivector error` 当成 Cube 侧 Fixpipe 参数错去反复改 `FixpipeParamsV220.srcStride`，未先查核类型派发（本 trace 子 agent 一度怀疑 Fixpipe srcStride，绕路后才定位到 MIX 派发）。
- 在入口不加任何核类型标记的情况下，仅靠"代码里只调 Cube API"期望编译器自动识别——bisheng 不会据此推断为纯 Cube，仍按 MIX 编译。

## 失效边界

- CANN 9.1.0 头文件未暴露 `__cube__` 函数级标记，`KERNEL_TASK_TYPE_DEFAULT` 宏是当前唯一编译期标记途径；后续 CANN 版本若暴露 `__cube__`，做法可能变化。
- 950（Ascend950）**仿真器**无法验证本判别是否在 950 真实硬件上也成立——cannsim Ascend950PR 不支持 Cube 核直调 kernel 执行（见相关独立卡）；需在真实 Ascend950 卡上复验。950 真实芯片：未验证，推断可迁移。
- A2（dav-200）：未验证，推断可迁移（同样有 Cube/AIV 区分）。