---
type: Concept
title: "Ascend950 每核存储层次与 UB 双口径"
description: "950 系列（PR/DT 共架构）每 AI Core 的 L1/L0A/L0B/L0C/UB 容量；UB 512KB/AI Core 标称总量（白皮书表4-2 口径）vs 248KB/AIV 软件可用（CANN 平台配置口径）的双口径澄清——kernel authoring 和 tiling 预算以 248KB 为安全天花板，代码必须 GetCoreMemSize(UB) 不得硬编码。"
tags: [task.implementation, topic.architecture, topic.memory, topic.tiling]
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
  - resource: https://gitcode.com/cann/cannbot-skills/blob/bb96c9c595c7a8e96745d365291769dc48319c22/plugins-community/ascendc-port-orchestrator/kb/okf/runbooks/field-notes/build/pb-32-simt-dcache-shares-ub-tiling-must-reserve-40kb-or.md
    role: primary
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950-per-core-memory]
---

# Ascend950 每核存储层次（PR/DT 共架构）[SPEC p25 表4-2]

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


| 存储 | 容量 | 来源 |
|---|---|---|
| L1 Buffer | **512 KB / AI Core** | [SPEC p25] |
| L0A Buffer | **64 KB / AI Core** | [SPEC p25] |
| L0B Buffer | **64 KB / AI Core** | [SPEC p25] |
| L0C Buffer | **256 KB / AI Core** | [SPEC p25] |
| **Unified Buffer (UB)** | **512 KB / AI Core（标称）** | [SPEC p25] |
| CPU L1 Cache | 64 KB / CPU Core | [SPEC p25] |
| CPU L2 Cache | 1 MB / CPU Core | [SPEC p25] |
| L3 Cache | 4 MB / CPU Cluster | [SPEC p25] |

## UB 双口径澄清（两个权威数字、不同口径——不是矛盾）

- 白皮书的 **512 KB / AI Core** [SPEC p25 表4-2] 是标称硬件总量，物理上是两个 256 KB bank（UB0/UB1，各挨着一侧 Vector Core 的 Scalar 组 [SPEC p17 图4-1]）。
- CANN 安装的平台配置给出**每 AIV 可用** UB：`ub_size = 253952` 字节（**248 KB**）[Ascend950DT_9582.ini，CANN 9.1.0 `aarch64-linux/data/platform_config/`]。
- **kernel authoring 与 tiling 容量预算以 248 KB 为安全天花板**（与 KB 的 OL-265 248KB 预算一致）。
- 代码必须用 `GetCoreMemSize(UB)`，绝不硬编码。
- SIMT（L3/regbase）核还要再从 UB 顶部预留 40KB（`SIMT_UB_SIZE_BYTE` 40960）给 SIMT DCache/线程态 → SIMT 有效 UB ≈ 208KB；按满容量做 SIMT tiling 会静默 UB 越界——见 [PB-32](../../../ops/ascendc/runbooks/compilation/pb_32_simt_dcache_shares_ub_tiling_must_reserve_40kb_or.md)。

相关：[950DT 主卡](target_ascend950dt.md)、[950PR 平台卡](target_ascend950pr.md)、[NPU 存储模型](npu_memory_model.md)、[roofline 模型](../../../ops/ascendc/concepts/roofline_model.md)。
