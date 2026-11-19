---
type: Guide
title: Profiler Host 诊断：GC 阈值、系统采样与缺失事件
description: 按 GC、进程 CPU/内存、系统网络及 OSRT 分开采样，记录依赖和开关被回退的条件。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/trace_view_GC.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/trace_view_GC.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: constraint
created_at: '2026-11-09T03:21:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler Host 诊断：GC 阈值、系统采样与缺失事件

## 版本与任务

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，限定已声明产品支持的 A2/A3 采集路径。两仓主线提交不自动构成兼容软件栈；不回推为 26.0/PyTorch2.8 的默认值或完整能力。


## GC 不等于设备释放

gc_detect_threshold 默认 None，关闭检测；非负数表示采集超过阈值的 Python GC 事件，单位 ms。0 表示所有事件，可能产生大量数据，来源建议从 1ms 开始。GC 是 Python 回收行为，与 NPU 分配器实际归还、Kernel 完成是不同事件。

结果可在 trace_view.json 的 GC 层或 GC_RECORD 表查看；表内 startNs/endNs 单位 ns，globalTid 指示进程/线程。阈值为 ms，记录为 ns，比较前先换算。没有超过阈值的事件或没有开启检测，不能推断该进程完全未发生 GC。

固定 TorchNPU 实现会把非数值或负阈值重置为 None 并打印提示；因此“传入了一个参数”不等于采集已开启。注意检查最终配置与日志。

## host_sys 按瓶颈选项采集

host_sys 必须为列表；默认空。CPU、MEM、DISK、OSRT 是进程级 CPU 利用率、内存利用率、磁盘 I/O、syscall/pthreadcall；NETWORK 是系统级网络 I/O，不能全归因到模型进程。固定 PyTorch 指南和实现还包含 NUMA，可观察本地/远程读带宽及比例；OpPlugin 的枚举说明未列出它，部署时需确认实际 HostSystem.NUMA 成员。

固定实现中列表类型不对，或包含任何不支持成员，会将整组 host_sys 清空；不要以为只有错误成员被忽略。

## 工具和环境会改变采样结果

DISK 需要 iotop；OSRT 需要 perf/ltrace 及相应权限配置，重新安装 CANN 后需重新核对权限。ltrace 可显著提高 CPU 占用并扰动 pthread 加解锁，不能直接把这种观测开销当业务原有成本。

来源对 KylinV10SP1 的 OSRT 约束区分架构：x86_64 支持，aarch64 不支持；虚拟化 Euler2.9 不支持 NETWORK。这里仅转述所列环境，不推导其他系统版本均支持。

将 Host 空洞与 CPU、GC、I/O、设备排队时间对齐，再以关闭相应采样的对照确认归因。


## 结果核验

检查实际配置、采集窗口、rank/device 和导出模式，再检查文件及表是否存在；未采集或未关联不等于数值为零。关闭高成本观测后复测正常负载。本文没有运行采集、数据库查询或 NPU 性能实验。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)
- [数据库关联和时间单位](torch_npu_profiler_database_relations.md)

## HostSystem成员的发布边界

发布experimental_config.py的HostSystem没有NUMA，主线增加该成员；两版均会在任何一个host_sys成员非法时清空整组，因此向发布包传入主线新增成员可能同时失去其他系统项。GC还需要CPU活动，阈值被接受不保证实际事件超过阈值。配置清单与版本差异见[_ExperimentalConfig API](../../../apis/torch_npu/profiler_experimental_config.md)。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/experimental_config.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/trace_view_GC.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/trace_view_GC.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/experimental_config.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（constraint）
