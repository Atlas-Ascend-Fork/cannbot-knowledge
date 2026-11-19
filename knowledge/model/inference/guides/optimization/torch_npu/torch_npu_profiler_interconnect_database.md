---
type: Guide
title: Profiler 互连数据库：NIC/RoCE、HCCS 与 PCIe 采样口径
description: 区分设备端口采样与 HCCL 算子统计，解释速率、累计计数、吞吐及 PCIe 时延单位。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
created_at: '2026-11-09T03:21:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 互连数据库：NIC/RoCE、HCCS 与 PCIe 采样口径

## 版本与任务

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，限定已声明产品支持的 A2/A3 采集路径。两仓主线提交不自动构成兼容软件栈；不回推为 26.0/PyTorch2.8 的默认值或完整能力。


## 先区分采集开关和分析对象

_ExperimentalConfig(sys_io=True) 控制 NIC、RoCE、MAC 采集，默认 False；sys_interconnection=True 控制 HCCS、PCIe 等片间传输采集，默认 False。来源的汇总 DB 表格定义了 ROCE、NIC、HCCS、PCIE；MAC 开关存在不表示本卡已经定义独立 MAC 表。

这些是设备/端口随时间的采样，不是每个 HCCL 算子的独占传输统计；分析通信操作仍须结合 analysis.db 的 rank 对、通信名称和窗口。HostSystem.NETWORK 的系统级网络数据也不是相同对象。

## ROCE 与 NIC

deviceId 确定设备，funcId 为端口号，timestampNs 为本地时间 ns。bandwidth 为 Byte/s；rxPacketRate/txPacketRate 为 packet/s，rxByteRate/txByteRate 为 Byte/s。rxPackets/txPackets、rxErrors/txErrors、rxDropped/txDropped 为累计 packet 数，rxBytes/txBytes 为累计 Byte 数。

速率与累计计数不能直接混用；检查丢包/错误是否增长时应比较同设备同端口连续样本，并核对窗口、计数重置和采样缺口。单个累计值不能解释本轮模型独占流量。不同设备的“本地时间”也不能未经校准就视作同一全局时钟。

## HCCS 与 PCIe

HCCS 的 deviceId、timestampNs 定位样本，txThroughput/rxThroughput 为 Byte/s。它们与 analysis.db 中 GB/s、MB、ms 的通信统计有不同单位及聚合对象。

PCIE 的 tx/rx 两方向各有 Post、Nonpost、Cpl 的 Min/Max/Avg 传输带宽字段，单位 Byte/s；txNonpostLatencyMin/Max/Avg 是 ns。带宽与时延不能相加，Min/Max/Avg 也不是三个可以累计的流量。先确认方向、事务类型、设备、采样窗口再比较瓶颈。

## 归因与边界

带宽低可能是缺少传输、算子等待其他 rank、负载变化或采样未覆盖，不能单凭一张采样表判定链路故障。带宽高也不证明通信已被计算隐藏。核对实际配置、通信时间线、rank 到达和传输数据量。

本卡蒸馏上述四张表的采样职责与单位，不扩展未审阅的 msprof 硬件/操作系统支持矩阵。


## 结果核验

检查实际配置、采集窗口、rank/device 和导出模式，再检查文件及表是否存在；未采集或未关联不等于数值为零。关闭高成本观测后复测正常负载。本文没有运行采集、数据库查询或 NPU 性能实验。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)
- [数据库关联和时间单位](torch_npu_profiler_database_relations.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_ExperimentalConfig.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）
