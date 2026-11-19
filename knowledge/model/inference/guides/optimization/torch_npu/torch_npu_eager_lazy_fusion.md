---
type: Guide
title: TorchNPU Eager DVM 融合：总开关、区间和提交边界
description: 说明不经 torch.compile 的小算子融合、脚本开关与转储门实现层、环境变量实际解析面及进程级线程限制。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/TORCH_NPU_LAZY_FUSION.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/TORCH_NPU_LAZY_FUSION.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/lazy_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/lazy_fusion.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.h
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp
  role: implementation
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# TorchNPU Eager DVM 融合：总开关、区间和提交边界

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 开启的必要条件

TORCH_NPU_LAZY_FUSION=True 在 Eager 下将相邻小算子融合，默认未配/False 关闭，无需 torch.compile。必须在 import torch_npu 前开启总开关，并满足 TASK_QUEUE_ENABLE=1/2；否则自动禁用。仅在 DVM 支持型号、主线程及其反向线程生效，其他独立线程自动禁用。本卡只选文档产品表列出的 A2/A3，不由 DVM 其他文档扩展到 950。

## 代码区间和恢复

torch_npu.npu.lazy_fusion.enabled()/disabled() 上下文支持嵌套，正常或异常退出都恢复进入前状态；set_enable()/set_disable() 无参数、返回 None，直接修改后持续生效，不会自动恢复。两种方式混用时，上下文退出仍恢复进入前状态，即使内部调用了直接设置。

环境变量未开启时，enabled/set_enable 不能独立启用融合。开关变化会提交当前待融合图，防止跨区间融合；提交不等待设备计算完成，因此不能把退出上下文当作同步点。状态是进程级，切换时不要并发构建融合图。

## 评估

在小算子密集、Host 下发明显的区间评估，保留边界外原有依赖与 Tensor 生命周期；比较端到端收益、融合 kernel 及数值。它与 Inductor DVM 编译模式是不同入口，不混用开关或据名称相同推定相同优化路径。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/performance_tuning/TORCH_NPU_LAZY_FUSION.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/performance_tuning/TORCH_NPU_LAZY_FUSION.md)（constraint）


## 脚本侧开关与转储门：torch_npu 实现层（增补）

旧正文按文档页描述 `lazy_fusion.enabled()/disabled()/set_enable()/set_disable()`。本节补上文档页没有的实现层：Python 门面 `torch_npu/npu/lazy_fusion.py`（经 `npu/__init__.py:172` 导出）与 csrc 绑定 `torch_npu/csrc/npu/lazy_fusion.cpp`（`THNPLazyFusion_init` 由 InitNpuBindings.cpp:258 挂载到 `torch_npu._C._lazy_fusion`，`#ifndef BUILD_LIBTORCH`）。两个绑定 `_set_disabled(disabled)`/`_set_dump_enabled(enabled)` 直接转发 op-plugin 的 `lazy_fusion::SetLazyFusionDisabled/SetLazyFusionDumpEnabled`（lazy_fusion_control.h:21-24），并**返回进入前的旧状态**——上下文恢复不是 Python 侧记快照，而是用该返回值在 finally 中回写（lazy_fusion.py:47-51/:94-98），因此 `enabled()`/`dump_enabled()` 参数非 bool 时在进入时即 TypeError（:45-46/:93-94）。

除旧正文的四个融合开关外，模块还导出文档页未提的**转储门**：`set_dump_enable()/set_dump_disable()/dump_enabled()/dump_disabled()`（lazy_fusion.py:59-107）。转储门与融合门共用环境总开关和同一提交边界语义（docstring 自述：状态变化提交当前待融合图；已排队图保留其创建时的转储状态，含 codegen 在 task-queue 线程执行的情形）。op-plugin 侧实现在 `g_lazy_fusion_manager`：脚本门 `dump_enabled_` 原子量默认 **true**（lazy_fusion_kernel.h:410），`SetDumpEnabled` 变化时先 `Flush()` 再交换并返回旧值（lazy_fusion_kernel.cpp:188-193）；每个融合 kernel 在 Reset 时快照 `flags_.dump_as_text && dump_enabled_`（lazy_fusion_kernel.h:365），kernel 自身按 `ShouldDump()` 决定是否写文本（:63）——**文本转储需要 env `dump_as_text` 与脚本门同时开启**，只开脚本门不改变未带 dump_as_text 的环境。`SetLazyFusionDisabled` 同样在变化时 `LazyFusionFlush()` 并返回旧值（lazy_fusion_kernel.cpp:166-173）。转储目录按 `dump_dir` 创建，创建或 realpath 失败时仅告警并置 `enable_dump_=false`（:134-153）。

## TORCH_NPU_LAZY_FUSION 的实际解析面（增补）

中英文文档页只写 True/False。op-plugin 主线的实际解析（lazy_fusion_flags.cpp:196-249，`LazyFusionFlags` 构造时读一次 env）：

| env 内容 | 实际行为 |
| --- | --- |
| unset 或全空白 | 关闭 |
| 头 token 是 bool 字面量（True/true/1/on/TRUE；False/false/0/off/FALSE） | 头 token 决定开关；False 直接关闭并停止解析剩余 |
| 头 token 不是 bool 字面量（如 `level=O1`） | **存在即启用**，整串作为 flag 列表解析 |
| flag 列表 | 空格分隔，`key`（裸 bool，等于 true）或 `key=value`；`--` 前缀 token 无效 |

注册的 flag：`dump_as_text`（bool，默认 false）、`dump_dir`（默认 `./lazy_fusion_dump`）、`synchronize`（默认 false）、`online_tuning`（默认 false）、`disable_ops`/`enable_ops`/`enable_ops_only`（逗号分隔名单）、`foreach_max_tensors`（默认 8）、`foreach_min_numel`（默认 65536）、`level`（O1/O2，内部调试用途）。bool 值额外接受 true/True/on/1 与 false/False/off/0，其余值告警并保持默认；重复 flag 告警且首个生效；未注册 flag 告警 Unknown。`level` 头注释声明其为 internal-debug、裸 `O1`/`O2` 会被拒绝——实际行为是把裸 token 当未知 flag 告警并保持默认，**总开关仍为启用**。O1/O2 的算子集合按头注释：O1 为保守集（elementwise/激活/where/batch-norm 前向/foreach），O2 为 O1 加 matmul/mm/bmm/addmm/sum/native_batch_norm_backward/npu_swiglu；`True` 默认 O2。逐算子是否真正融合由 op-plugin DVM 执行层决定，本卡未核对各 op 的融合实现。

版本边界：torch_npu 发布 pin 无 `npu/lazy_fusion.py`、`csrc/npu/lazy_fusion.cpp`（固定树内检索无匹配），op-plugin 发布 pin 无 `ops/dvm/` 目录——整条脚本面与解析面是主线独有。本卡分别引用独立冻结的 torch_npu 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与 op-plugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`；来源固定不证明跨仓配套或其他组合可用。

## 补充来源

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/lazy_fusion.py)（primary）：全文 1–107。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/lazy_fusion.cpp)（primary）：全文 1–33。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp)（implementation）：行段 215–260（声明 :217 与挂载 :258）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）：行段 1–30、165–175（__all__ 导出 lazy_fusion 与导入点）。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_control.h)（primary）：全文 1–24（跨仓控制面契约）。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.h)（primary）：全文 1–59（Level 枚举与全部默认值）。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_flags.cpp)（primary）：全文 1–249（env 解析与 flag 注册）。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.h)（implementation）：行段 40–70、310–370、405–412（Reset/ShouldDump、Manager::Get 的流切换 Flush 与转储快照、dump_enabled_ 默认）。
- [固定源码](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/dvm/lazy_fusion_kernel.cpp)（implementation）：行段 125–205（CreateDumpDir、SetLazyFusionDisabled/SetDumpEnabled）。
