---
type: Concept
title: "Ascend950DT 实测观测与方法学警告"
description: "一台 950DT 主机的实测值（CANN 9.1.0, 2026-09-05）：matmul fp16/bf16 430.4 TFLOP/s、HBM 大缓冲平台期 2.7–3.1 TB/s、conv fp16 353–364、conv fp32 HF32 开 176–183/关 26.9；测量陷阱：小缓冲带宽假象、matmul 不能当 conv 上限、SKU 未定。"
tags: [task.optimization, topic.performance.analysis, topic.architecture]
status: draft
sources:
- resource: https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf
  role: supporting
created_at: "2026-09-22T04:15:00Z"
updated_at: "2026-10-16T00:00:00Z"
platforms: ["950"]
aliases: [hw/ascend950dt-measured]
---

> **来源说明（2026-10-16）**：本卡实测数字来自车队私有单机测量（[MEASURED]），无公开复核途径，按社区评审要求维持 draft；卡内 [SPEC] 对照指向的白皮书已有官方公开版（见 sources），该部分可直接复核。待实测部分补可复核来源后回升。

# Ascend950DT 实测观测（单主机，[MEASURED]，非规格非上限）

> **[SPEC 引用说明]** 本卡中 `[SPEC pN §x 图y]` 标注指向[《昇腾 950 NPU 架构白皮书》官方公开版](https://public-download.obs.cn-east-2.myhuaweicloud.com/ascend/%E6%98%87%E8%85%BE950%20NPU%E6%9E%B6%E6%9E%84%E7%99%BD%E7%9A%AE%E4%B9%A6.pdf)（SHA-256 `ece3405e6a17fabdd462338fb94266558649a6407a2f28008403211387b3a927`；页码按 PDF 文件页序、从 1 开始）。该标注表示该字段属"厂商主张"证据层（非实测、非承诺）；可实测核对的内容以各卡 `[MEASURED]` 标注与正文数据为准。


⚠️ 以下全部数字 [MEASURED]：一台内部 A5 主机，CANN 9.1.0，torch_npu，2026-09-05，设备自报 `Ascend950DT_9582`。换个主机/驱动/CANN 构建/负载形状都可能不同。

| 量 | 观测值 | 方法 |
|---|---|---|
| matmul fp16 | 430.4 TFLOP/s | `torch.matmul` 8192³，30 次中位，2.555 ms |
| matmul bf16 | 430.4 TFLOP/s | 同上；与 fp16 四位有效数字相同 |
| matmul fp32 | 27.0 TFLOP/s | 同形状；未走 HF32 路径 |
| HBM 带宽 | ≈2.66–3.08 GB/ms（2.7–3.1 TB/s） | 1024 MB 下 copy / triad / read |
| conv fp16 | 353–364 TFLOP/s | `F.conv2d` 1x1 大形状 |
| conv fp32, HF32 ON | 176–183 TFLOP/s | `torch.npu.conv.allow_hf32=True` |
| conv fp32, HF32 OFF | 26.9 TFLOP/s | 开/关比 = 6.70× |

## 方法学警告（会改变数字的事）

- **不要引用跨缓冲尺寸的最大带宽**：64 MB fp32 copy 实测 4874 GB/s，是大缓冲平台期的 ~1.8×（缓存驻留是 plausible 解读，未证实）。报告用 ≥1024 MB 的大缓冲平台期。
- **`torch.matmul` 不是 conv 参考的正确仪器**：conv fp16 到 353–364 而非 430.4；fp32+HF32 到 176–183 而 fp32 matmul 只有 27.0。拿 matmul fp16 当 fp32 参考的分母会把 conv 参考效率低估 ~2.35×。
- `torch.npu.matmul.allow_tf32` 在该构建上读出 `None`（赋值无效）；`torch.npu.conv.allow_hf32` 有效（6.70×，回读确认）。
- 导出脊点：fp16-matmul 峰值 / 大缓冲平台期 ⇒ 约 140–162 FLOP/byte——只作量级排序参考，不构成任何具体 kernel 的有界性证明。

## 与规格表的交叉对照

实测 430.4 TFLOP/s fp16 matmul 最接近 [SPEC p13 表3-1] 的 28-Cube DT SKU 行（BF16/FP16=425）——与该主机是 28 核 SKU 一致，但**不是证明**（SKU UNKNOWN 仍然成立，见 [差异卡](ascend950dt_vs_pr_overrides.md)）。

## 两个"借来的数字"警告

- 旧设计文档里的 4 TB/s 来自公开产品线路线图，不是本 SoC 的实测。
- [950PR 页](target_ascend950pr.md)的 ~1.1 TB/s 是在 950PR 上另一组实测配置测得。950PR（prefill）与 950DT（decode）是同芯片的不同产品模式；1.1 vs ~2.7 TB/s 的差距不归因于任何单一原因。

相关：[roofline 模型](../../../ops/ascendc/concepts/roofline_model.md)（PR 侧实测峰值）、[950DT 主卡](target_ascend950dt.md)。
