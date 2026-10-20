---
type: Concept
title: "Ascend950DT_9582 -- Target Platform (950DT)"
description: "Ascend950DT 目标平台主卡：与 950PR 共架构、内存/SKU 级差异；两级证据标注约定（SPEC/MEASURED）；子卡索引：差异表、每核存储层次、微架构、调度/互连、实测数据。"
tags: [task.lookup, topic.architecture, topic.memory]
status: stable
sources:
  - resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
    role: primary
  - resource: https://gitcode.com/Ascend/triton-ascend/blob/c22984baa55e1506eadd7c72955d9bf669b1c959/third_party/ascend/backend/runtime/cv_autotune/hardware_consts.py
    role: implementation
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/hardware/target-ascend950pr.md
    role: primary
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/reference/porter/handbook/roofline_model.md
    role: primary
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950dt]
---

# Ascend950DT_9582 — Target Platform (950DT)

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


**证据两级标注约定（读本族任何卡都先读这段）**：

- **[SPEC pN]** — [《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`）第 N 页（PDF 文件页序）。规格是设计包络，不是任何具体主机的实测。
- **[MEASURED]** — 在某一台具体主机上实测（CANN 9.1.0，2026-09-05，方法注明）。主机/驱动/CANN 构建/负载相关，不是厂商保证也不是上限。

**950PR 与 950DT 是共架构、内存/SKU 级差异**——不是两颗芯片。厂商原文 [SPEC p10 §3]："昇腾 950PR 芯片和昇腾 950DT 芯片采用共架构设计，通过搭载不同的片上内存，实现在细分应用场景上的竞争力提升"。差异表未列的字段全系通用。

## 子卡（按主题拆开，按需沿链阅读）

- [DT↔PR 差异与 SKU 表](ascend950dt_vs_pr_overrides.md)——片上内存容量/带宽（headline 差异）、SKU 核数、分格式算力表、L2、AI CPU
- [每核存储层次与 UB 双口径](ascend950_per_core_memory.md)——L1/L0A/L0B/L0C/UB 容量；**UB 512KB/AI Core 标称总量 vs 248KB/AIV 软件可用的双口径澄清**（tiling 预算天花板）
- [微架构（Cube/Vector/CV 通道/NDDMA/BufferID）](ascend950_microarchitecture.md)
- [调度器 / 互连 / DVPP](ascend950_scheduler_interconnect.md)——STARS2.0、UB 2.0、URMA、CCU、PCIe、DVPP
- [950DT 实测观测与方法学警告](ascend950dt_measured_observations.md)——单主机实测值、测量陷阱（大缓冲平台期 vs 缓存驻留假象、matmul≠conv 上限）

相关：[950PR 平台卡](target_ascend950pr.md)（同系列对照）、[910_95/950 前代速查](ascend_910_95.md)（同族参照）、[NPU 存储模型](npu_memory_model.md)、[roofline 模型](../../../ops/ascendc/concepts/roofline_model.md)（实测峰值与脊点）。
