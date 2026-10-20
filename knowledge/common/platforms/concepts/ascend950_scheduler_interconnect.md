---
type: Concept
title: "Ascend950 调度器 / 互连 / DVPP"
description: "950 系列共架构：STARS2.0 硬件调度器（任务流/资源池/同步标志）；UB 2.0 互连（HiLink SerDes、UBoE、URMA、CCU 集合通信、片上交换）；PCIe 5.0；DVPP 编解码配置。"
tags: [task.lookup, topic.architecture]
status: stable
sources:
- resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
  role: primary
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950-scheduler-interconnect]
---

# Ascend950 调度器 / 互连 / DVPP（950PR/950DT 共架构）

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


## STARS2.0 调度器 [SPEC p27 §4.4]

硬件任务/资源调度器：Host-offload 最多 2048 任务流；最多 16 AI-CPU + 64 Host-CPU 并发任务；64 UB jetty；32 CCU 任务；32 SDMA 通道；128K 1-bit / 4096 32-bit 同步标志；HSCB 低延迟 AIC/AIV 控制总线；最多 8 调度 Group；最多 16 资源池。

## 互连 [SPEC p15 表3-1; p30–35 §4.6]

- UB 2.0；72 Lane HiLink SerDes（每 Lane 最高 112 Gbps）划分为 18 个 x4 端口（双向 2016 GB/s，光模块限制）；UBoE 2×400 Gbps（与 UB 共享 2 端口），端口拆分 1×400/200/100/50/25 或 2×200/100/50/25 Gbps。
- URMA 异步（Jetty SQE/CQE，Write/Read/Send/Atomic；RTP 模式 4 端口可靠，CTP 模式 9 端口）；UB Memory 同步（Load/Store/AtomicStore/AtomicLoad/AtomicSwap/AtomicCompareAndSwap）。
- CCU 集合通信引擎（Broadcast/ReduceScatter/AllGather/AllReduce/All2All/All2Allv）。
- UB 片上交换（每 IO Die 9 个 x4 端口转发，不走 DRAM）。
- PCIe 5.0 x16（双向 128 GB/s，EP/RC、DMA、MCTP）。

## DVPP [SPEC p28 §4.5]

4× VPC + 4× JPEGE + 8× JPEGD；最大分辨率 32768×32768；JPEGD 等效 libjpeg-turbo v2.0.2；STARS 直接调度。

相关：[微架构](ascend950_microarchitecture.md)、[每核存储层次](ascend950_per_core_memory.md)、[950DT 主卡](target_ascend950dt.md)。
