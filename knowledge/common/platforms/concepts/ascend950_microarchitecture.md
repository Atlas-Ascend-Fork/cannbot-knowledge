---
type: Concept
title: "Ascend950 微架构（Cube/Vector/CV 通道/NDDMA/BufferID）"
description: "950 系列共架构微架构：芯片组成（2 AI Die + 2 IO Die）、Cube Core 与数值行为、Vector Core 双发射 SIMD、SIMD/SIMT 混合编程、Cube↔Vector 直通通道、NDDMA 五维重排、BufferID 同步原语、L2 特性。"
tags: [task.lookup, topic.architecture]
status: stable
sources:
- resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
  role: primary
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950-microarchitecture]
---

# Ascend950 微架构（950PR/950DT 共架构）

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


## 芯片组成 [SPEC p12 §3]

每片 2 AI Die + 2 IO Die；AI Die 承载 AI 子系统、L2、Linx816 CPU；IO Die 承载 UB/PCIe/DVPP/安全。D2D Clink + 内存接口拼成一个 UMA 整体。（DT 仅片上内存模块数不同——见 [差异卡](ascend950dt_vs_pr_overrides.md)。）

## AI Core 微架构

- **Cube Core**：16×16×16 FP16（图4-1）；MXFP8/HiF8/FP8/MXFP4 原生；同频下 FP8/FP4 2×、MXFP4 4× FP16 算力；更大 L0C 供 GEMM/FlashAttention tiling；Cube→UB 路径上在线 FP32→BF16/FP16/FP8/INT8 量化与 NZ↔ND/DN 重排 [SPEC p17 §4.1.1 及图4-1]。
- **Vector Core**：双发射寄存器 SIMD，RegFile 作 UB↔ALU staging [SPEC p21]；FP16/FP32 算力较上代 +100% [SPEC p20 §4.1.2]；BF16 原生 + 扩展转换指令 [SPEC p21]；Softmax/GELU 调优微架构 [SPEC p21]。
- **SIMD/SIMT 混合编程**：SIMD 为主，SIMT 处理不规则 gather/scatter/分支段；按 Vector-Function 选模式并快速切换 [SPEC p21 §4.1.3]。
- **Cube↔Vector（CV）直通通道**：Cube L1 与 Vector UB 直连，减少 L2 层数据交换；路径上带精度与布局转换 [SPEC p22 §4.1.4]。
- **NDDMA**：最高 5 维全局内存重排进 UB，硬件地址生成，内部 cache 把元素级读聚合成 128B 访问 [SPEC p23 §4.1.5]。
- **BufferID 同步**：`get_buf()`/`rel_buf()` 获取/释放替代 `set_flag`/`wait_flag` 对，比 flag-管线耦合更紧 [SPEC p23 §4.1.6]。

## AI CPU 子系统

Linx816（ARMv8-A，物理双线程，每核可配 1T/2T），每核共享 L1/L2，L3 4MB/cluster，与 AI Core L2 硬件一致 [SPEC p24 §4.2; p25 表4-2]。

## L2 Cache 特性

128 MB（DT）；多 bank、512B 线、4×128B Sector Cache（128/256B 访问高效）、per-bank 并发读写、L2-hint allocate/victim 策略（如 non-allocate bypass）、经 SDMA 的 CMO（Prefetch/Writeback/Invalid/Flush）[SPEC p26 §4.3.2; p15 表3-1]。

相关：[每核存储层次与 UB 双口径](ascend950_per_core_memory.md)（容量数字）、[调度/互连/DVPP](ascend950_scheduler_interconnect.md)、[950DT 主卡](target_ascend950dt.md)。
