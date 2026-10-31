---
type: Guide
title: InternVLA-N1：A2 上的 VLN-CE 评测与断点续跑
description: 固定随机性、视觉注意力分段语义和评测分母，按先分片后过滤组织 InternVLA-N1 的可恢复 R2R/RxR 评测。
tags:
- task.testing
- topic.model_architecture
- topic.attention
- topic.data_pipeline
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/docs/navigation/internvla-n1/infer_with_torch/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/navigation/internvla-n1/infer_with_torch/README.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/merge_requests/159
  role: evidence
created_at: '2026-10-29T04:09:08Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- a2
---

# InternVLA-N1：A2 上的 VLN-CE 评测与断点续跑

## 适用范围与产物

固定样例针对 Atlas A2 aarch64、无 NVIDIA GPU 的 VLN-CE 路径。产物包含固定软件/数据/种子、每 episode 结果、稳定分片、合并分母及统计区间。来源中的端到端数字是作者报告，本批未复测。

## 环境与可复现基线

在首次设备构造前完成 transfer_to_npu，语言模型使用 SDPA；Habitat 的 EGL 与软件渲染另行适配。来源使用 habitat-lab 0.2.4 与源码编译 habitat-sim 0.3.3，推理与 Habitat 环境通过受控 bridge 组合，不能任意升级 gym/numpy。System 1 的扩散噪声依赖 torch RNG，需在构建模型和设备迁移的合适时点固定种子。来源的 R2R 全量评测使用 CANN 9.0.0，RxR 全量使用 CANN 9.2.0；同批 1892 条 RxR 在两台机器上仅 2.5% 的 episode 六项指标逐位一致。CANN、重新编译的 habitat-sim、Mesa 及其他环境差异均可能影响结果，固定种子不能保证跨环境逐 episode 一致。

## 视觉注意力与数值验证

视觉塔原 SDPA 路径会显式构建分段块对角 mask。对应的变长注意力可用 TND 与累计长度表达；需同时保持图像与窗口分段，不能把所有图块作为一个互相可见的序列。

来源报告单次 System 2 generate 约 2.60→0.35 秒，闭环 episode 约 2.4 倍，但两者是不同指标。bf16 融合会有数值差异；必须比较算子误差、参考路径及全量任务指标。小样本 SR 下降不能独立证明实现错误或精度通过，靠近论文数字也不能替代跨实现逐项核验。

## 分片、续跑与分母

每张卡独立 world_size=1 进程，先按稳定全集切片，再按本分片 progress 过滤完成项；先过滤再切片会改变续跑归属。续跑显式使用原 OUT_ROOT，并保持首次运行的 NUM_NPU、--sample/--limit、--seed 和融合视觉注意力开关不变；采样发生在分片之前。改变这些条件会改变分片归属或数值路径。合并时检查预期 episode 数与唯一性。

RxR 英文子集 3669 条中，来源发现 99 条目标不可达，过滤后主表分母为 3570。合并必须打印每个指标的实际分母，并区分剔除与按失败计入的口径；不能静默过滤 NaN/Inf 后仍声称所有指标覆盖相同全集。源 R2R 全量为 1839 条。

## 验证、回退与停止条件

先验证环境 import、episode schema、有限值处理与稳定续跑，再固定种子做视觉 Attention A/B 和全量评测。缺数据、漏片/重复、分母变化未解释或数值超阈值时停止对比；回退到固定参考路径并保留原始 episode 输出。优化前全量耗时约 38 小时属于推算，不能列成实测基线。
