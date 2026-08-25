---
type: "Runbook"
title: "自定义算子内 .to(FP8) 多流跨流竞争 banned"
description: "多流 prefill 下自定义 NPU 算子内调用 .to(float8_e4m3fn) 触发 aclnnCast 跨流竞争 yHalf，507035=1028，该路线 banned。"
tags: ["task.debugging", "topic.implementation.synchronization", "topic.compute.quantization"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 自定义算子内 .to(FP8) 多流跨流竞争 banned

## 现象

deepseek-v4 模型 NPU 推理（Ascend950PR / dav-3510，CANN 9.1.0）在 prefill 阶段开启 `enable_multi_streams=True`。自定义 `DynamicBlockQuant` 算子的 host 胶水层先用 `aclrtLaunchKernel` 在当前 NPU 流上启动 AscendC kernel 产出 `yHalf`（half），再调用 `yHalf.to(at::kFloat8_e4m3fn)` 把输出转成 FP8 返回给模型。同步模式（`ASCEND_LAUNCH_BLOCKING=1`）下 `model run success`；切到多流模式后 `[rank0] [ERROR] ... 507035` 反复出现、`model run success=0`，错误异步归因到 `DynamicBlockQuantNpuOpApi.cpp` 和后续 `hc_post` 算子。kernel 本身的 `[KERNEL-REPLACE] DynamicBlockQuant` 打印正常出现。

## 适用场景

- **工程形态**：kernel 直调（`aclrtLaunchKernel` 直接启动）+ host 胶水层做 dtype 转换；算子返回类型与模型期望类型不同时，在算子内部 `.to()` 收口。
- **API 路径**：`aclrtLaunchKernel` 启动自定义 kernel → `tensor.to(at::kFloat8_e4m3fn)` → 触发 `aclnnCast`。
- **验证过的平台与 CANN 版本**：Ascend950PR（dav-3510），CANN 9.1.0。
- **适用粒度**：`operator_family`（任何"自定义 NPU 算子内用 `.to()` 做 FP8 / 跨流 dtype 转换"的实现都受此限制）。
- **路线优先级**：`banned`（多流模式下，在自定义算子内部对 `aclrtLaunchKernel` 产出的 tensor 做 `.to(float8_e4m3fn)` 是 banned 路线）。
- **不适用或未验证场景**：同步模式（`ASCEND_LAUNCH_BLOCKING=1` / 单流）下 `.to()` 正常工作；`.to()` 在算子外部、或在不开启 `enable_multi_streams` 的推理中未触发此问题。a2/a3 未验证。

## 失败路线

**banned**：在自定义 NPU 算子内部对 `aclrtLaunchKernel` 产出的 tensor 调用 `.to(at::kFloat8_e4m3fn)`，在 `enable_multi_streams=True` 下必触发跨流竞争 507035。根因为两条路径被派到不同流且无显式同步：

1. `aclrtLaunchKernel`（直接 ACL 调用）把 kernel 提交到 `c10_npu::getCurrentNPUStream()` 返回的流 A；
2. `yHalf.to(at::kFloat8_e4m3fn)` 经 PyTorch dispatch 走 `aclnnCast`，被派到 PyTorch 当前流（多流上下文下可能是流 B），且未与流 A 建立事件依赖。

流 B 上的 `aclnnCast` 可能在流 A 的 kernel 写完 `yHalf` 之前就读 `yHalf`，数据竞争损坏输出，下游 `hc_post` 读到损坏 FP8 数据后报 507035。错误被异步归因到 `DynamicBlockQuantNpuOpApi.cpp` 是因为 `aclnnCast` / `aclnnDynamicBlockQuantV2` 是最后一个被 trace 的 CANN 算子，并非真正失败点——真正失败点是 `hc_post` 读到的损坏数据。

本 trace 内通过受控对照实验（实验 A 透传原生算子 / 实验 B 返回 half 不做 `.to()` / 实验 C 返回 FP8 做 `.to()`）确认 `.to()` 是触发因素；但各路 `grep -c 507035` 的 bash 输出被上游 redact，逐实验计数为 agent_reported，可核的 tool_observed 信号是聚合 tool_result 中 `507035=1028` 与 `model run success=0`（多流 + `.to()` 路线）对比最终透传路线的 `model run success`。

本 trace 内尝试过的下列"修复"均未根治，全部回退：

- 在 `.to()` 前加 `aclrtSynchronizeStream`：会阻塞 host、暂停多流流水线，`hc_post` 仍报 507035（流上下文被打乱）。
- 用 `at::empty` + `copy_` 替代 `.to()`：`copy_` 仍触发 `aclnnCast`，同问题。
- 用 `.cpu()`（D2H）+ CPU `.to()` + `.copy_()`（H2D）：D2H/H2D 往返破坏多流，推理变慢，仍 507035。
- `c10_npu::NPUStreamGuard` / `aclrtSetCurrentStream`：C++ API 不存在或无效。
- `c10_npu::getCurrentNPUStream().stream(true)`（clean queue）vs `stream(false)`：均无效。

trace 内未找到可在多流下保活 `.to()` 的改法；最终采用规避路线（透传原生 / host 侧 / 模型层关闭多流）。

## 验证信号

- 多流 + `.to(FP8)` 路线：聚合 tool_result 报 `507035=1028`、`model run success=0`（来源平台:950；证据等级:tool_observed）。
- 最终透传路线（`torch_npu.npu_rms_norm` / 原生 dynamic_block_quant 等）：`model run success`（来源平台:950；证据等级:tool_observed）。

## 预防

- 自定义算子内部不要做跨 dtype 的 `.to()`，尤其不要对 `aclrtLaunchKernel` 直接产出的 tensor 做 `.to(float8_e4m3fn)`。让 kernel 直接产出模型期望的 dtype，或把转换推到算子外部 / 模型层。
- 若必须在算子内转换，需在 `aclrtLaunchKernel` 与 `aclnnCast` 之间用 `aclrtCreateEvent`/`aclrtRecordEvent`/`aclrtStreamWaitEvent` 建立显式跨流依赖（trace 内未实现成功，列为遗留）。

## 误诊

- 曾把 507035 归因到 `hc_post` 算子本身的 bug，反复改 `hc_post` 无效。后经受控对照实验才确认 `hc_post` 只是读到被 `.to()` 损坏的 FP8 数据的受害者。
- 曾怀疑 `aclnnCast` 单独坏掉，单独跑 `.to()` 在 NPU 流上正常——说明 `aclnnCast` 本身不坏，坏在"自定义 kernel 流 vs `.to()` 派发流"的跨流竞争。

<!-- cannbot:related:start -->
## 相关

- [aclrtMemcpyAsync 局部源生命周期缺陷](aclrtmemcpyasync_use_after_free.md)（`related`）：《自定义算子内 .to(FP8) 多流跨流竞争 banned》明确“多流 prefill 下自定义 NPU 算子内调用 .to(float8_e4m3fn) 触发 aclnnCast 跨流竞争 yHalf，507035=1028，该路线 banned。”；它与《aclrtMemcpyAsync 局部源生命周期缺陷》的“直调算子把局部 std::vector 的 data 指针交给 aclrtMemcpyAsync 后立即返回，源码上无法保证 host 源存活到异步拷贝完成；该缺陷需独立修正，但现有 trace 未证明它是后续 507035 的唯一根因。”在实际调用参数、数据流或结果校验上直接衔接。
- [at::zeros 异步零初始化跨 stream 覆盖 kernel 写出](../precision/at_zeros_stream_kernel.md)（`same_topic`）：《at::zeros 异步零初始化跨 stream 覆盖 kernel 写出》说明kernel 直调算子的 host 层用 allocate_xpu_zeros_like（at::zeros）在 torch 默认 stream 异步零初始化输出 tensor，kernel launch 走 XpuRuntimeManager::get_ins<aclrtStream> 的 xpu_ops stream，两 stream 无同步；批量高负载下零初始化在 kernel 写入之后完成，整段 GM 写入覆盖 kv_a_out new 区。判别=BUGDIAG 按 region 分桶报 hist_zr=0 new_zr 非零 + 源码审查命中 allocate_xpu_zeros_like 且 kernel 在异 stream。；《自定义算子内 .to(FP8) 多流跨流竞争 banned》说明多流 prefill 下自定义 NPU 算子内调用 .to(float8_e4m3fn) 触发 aclnnCast 跨流竞争 yHalf，507035=1028，该路线 banned。。二者在at::zeros和直调kernel位于不同stream且无依赖，设备同步或同stream staging是防止零初始化覆盖写出的直接修复上存在可执行的直接衔接。
- [半精度 shadow 跨流竞态 — 转换与 kernel 两侧做设备同步](../precision/torch_npu_async_temporaries_need_completion_before_raw_kernel.md)（`same_topic`）：两卡都通过同步/多流 A/B 证明 PyTorch dtype 转换与 raw aclStream kernel 未建立依赖会产生跨流竞态；一张是 kernel 后 .to(FP8) 被过早读取，另一张是 cast 临时量在 kernel 前未完成。
<!-- cannbot:related:end -->
