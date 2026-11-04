---
type: Runbook
title: "torch::zeros 的零填充与裸 kernel 无流序"
description: "torch::zeros 的零填充不保证与随后 aclrtlaunch_* 同流；裸 kernel 可能读到未完成清零的旧数据，表现为首次正确、后续全零。改为 empty + 显式清零 + 紧贴 launch 的整机同步，或避免裸 launch。"
tags: [task.debugging, topic.implementation.synchronization, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/ol-66-torch-zeros-on-npu-is-not-stream-ordered-with-cust.md
    role: primary
created_at: "2026-07-09T16:00:00Z"
updated_at: '2026-10-29T05:07:58Z'
platforms: ["310p"]
aliases: ["OL-66"]
---

# torch::zeros 的零填充与裸 kernel 无流序

> 原 OKF v1 卡号：**OL-66**。
> 现象分类：运行时流序 / 精度；观测置信度：single_run（单次观测）。
> 触发信号：
> - custom AscendC kernel uses a torch::zeros tensor as output

## 现象

torch 扩展把 `torch::zeros` 分配的 NPU 张量作为 AscendC kernel 的输出缓冲，随后用裸 `aclrtlaunch_*` 启动 kernel：

```cpp
auto out = torch::zeros({B, T, H}, x.options().dtype(torch::kFloat32));
aclrtlaunch_scan_310p(blockDim, stream, x.data_ptr(), out.data_ptr(), ...);
```

连续多轮调用时第 0 轮结果正确、**第 1 轮及以后输出全零**；单独跑某一迭代不复现。无编译错误、无运行时报错。

## 适用场景

- 工程形态：torch 扩展 / AscendC kernel 直调，输出缓冲由 `torch::zeros` 分配、随后用裸 `aclrtlaunch_*` 启动 kernel。
- API 路径：`torch::zeros` / `torch::empty` + `zero_()`、`c10_npu::npuSynchronizeDevice()`、`aclrtlaunch_*`；框架原生 `copy_`/`to()` 作为替代路径。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0；历史卡另记录 310P + CANN 9.0.0 的单次观测。
- 适用粒度：`platform_wide`——任何“torch 分配 + 裸 launch”且 kernel 依赖输出初值的链路。
- 路线优先级：`recommended_fastpath`（优先不用裸 launch；必须用时，`empty` + 显式清零 + 紧贴 launch 的同步）。
- 明确不适用 / 未验证场景：全程走框架 dispatcher、无裸 launch 的链路不在本卡范围；其它代际的流序语义未验证。

## 根因

`torch::zeros` 的零填充与随后的裸 `aclrtlaunch_*` 之间没有流序保证：清零是异步 host 操作，裸 launch 不经过框架 dispatcher，不会自动插入同流依赖。kernel 若依赖输出缓冲的初值（先读后写/累加），就可能读到尚未清零的旧内容。

310P 上已验证的修法是 `torch::empty` + 显式 `zero_()` + 紧贴 launch 的 `npuSynchronizeDevice()`；旧卡给出的 `aclrtMemsetAsync(stream)` 路线在 310P 上未验证等价，不单独作为配方。

## 310P/CANN 9.1.0 补充（首次对、后续全零：empty + 整机同步 + 清零点）

310P（dav-m200）+ CANN 9.1.0 上复现并细化了本卡：`torch::zeros` 分配的 NPU 输出缓冲，其零填充与随后的裸 `aclrtlaunch_*` 之间没有流序保证。

- **症状指纹**：第 0 次调用结果正确，**第 1 次及以后全部为零**；单独跑某一迭代不复发，连续跑必现。原因是首轮缓冲恰好是干净的（新分配），后续轮次复用了未清零的旧内容，而 kernel 依赖"先读后写"的累加语义。
- **310P 上可用的写法**：`torch::empty` 分配 → 显式 `zero_()` → `c10_npu::npuSynchronizeDevice()` → 裸 launch；或保留 `torch::zeros`，但在裸 launch 前做一次整机同步。
- **同步位置**：必须紧贴裸 launch 之前，中间不能插入新的异步 host 操作；放在函数入口等于没放。

```cpp
// before：zeros 的零填充与裸 launch 无流序
auto out = torch::zeros({B, T, H}, x.options().dtype(torch::kFloat32));
aclrtlaunch_scan_310p(blockDim, stream, x.data_ptr(), out.data_ptr(), ...);

// after：empty + 显式清零 + 紧贴 launch 的整机同步
auto out = torch::empty({B, T, H}, x.options().dtype(torch::kFloat32));
out.zero_();
c10_npu::npuSynchronizeDevice();     // 紧贴 launch 之前
aclrtlaunch_scan_310p(blockDim, stream, x.data_ptr(), out.data_ptr(), ...);
```

## 验证信号

- 310P/CANN 9.1.0：连续多轮调用时，首轮结果正确、第 1 轮起输出全零；单轮调用不复现（来源平台：310P；证据等级：tool_observed）。
- 改为 `torch::empty` + 显式清零 + 紧贴 launch 的整机同步后，连续多轮不再出现全零（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 只在 310P + CANN 9.1.0 复现；其它代际/其它 torch_npu 版本的流序行为未验证。
- `npuSynchronizeDevice()` 是整机同步，每次调用都要付一次设备排空代价；只适合验证或低频入口，不适合热路径。
- 若 kernel 对输出每个元素都无条件写、且不先读旧值，本问题不会显现——不要因此认为 `zeros` 天然有序。
- 未验证 `aclrtMemsetAsync` + 同一 stream 的写法在 310P 上是否完全等价于旧卡结论。

## 坏实践

- 只用单次调用验证输出正确性（首轮恒为干净缓冲，必然通过）。
- 把同步放在函数入口或张量分配之前，中间又插入异步 op，然后宣布"同步无效"。
- 认为 `torch::zeros` 的零填充一定先于裸 launch 完成。

## 误诊

- 误诊：连续跑出现全零后，先怀疑 kernel 计算逻辑或输入数据（agent_reported）；"首轮对、后续全零"是流序指纹。
- 误诊：把问题归因于设备未复位/环境脏（agent_reported）；同一进程内新分配缓冲即可复现。

- 历史存量证据（agent_reported，非本 trace 复现）：旧卡记录一次直方图算子调试中“未加修复 5/5 失败、加修复 5/5 通过”；仅作历史参考，不作本 trace 验证信号。

<!-- 迁移自 porter OPERATIONAL_KNOWLEDGE.md OL-66（category=platform_bug，convert_ol_to_okf.py，M1）。confidence/severity/reproduce_count 未升格。 -->
