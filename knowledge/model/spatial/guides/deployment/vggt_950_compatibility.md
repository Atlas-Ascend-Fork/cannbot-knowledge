---
type: Guide
title: VGGT 迁到 950：跳过私有格式转换并检查 Attention 连续性
description: 根据具身智能仓已合入实现核对 950 加载、Q/K/V 连续化和无残差 LayerNorm 路径，保留旧 A2 性能与新平台验证的边界。
tags:
- task.migration
- topic.three_dimensional_reconstruction
- topic.memory
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/3d_vision/vggt/utils.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/3d_vision/vggt/demo_infer.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/3d_vision/vggt/vggt/layers/attention.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-embodied-ai/21a5ed789ceb2a4b72277573f5ec5ec531b92ee1/3d_vision/vggt/vggt/layers/block.py
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/merge_requests/133
  role: evidence
created_at: '2026-10-29T04:09:08Z'
updated_at: '2026-10-29T12:00:02Z'
platforms:
- '950'
---

# VGGT 迁到 950：跳过私有格式转换并检查 Attention 连续性

## 适用范围与预期产物

适用于固定具身智能仓中带 950 分支的 VGGT 实现。旧空间智能仓已归档，后续样例维护入口位于具身智能仓。产物应包含实际软件版本、加载路径、张量布局与目标设备的精度/性能验证。

## 三个适配点

1. 标准加载与序列并行加载在识别 950 时均跳过该样例的 conv-weight-layout-preconvert / cast_model_weight。不能把旧 A2 的私有格式预转换流程原样套到此分支，也不能据此推导整个 950 的所有算子都只支持一种格式。
2. Global Attention 的 FIA helper 在 950 分支先把 Q/K/V 连续化，覆盖该 helper 的 FIA 调用及训练 dropout 时的 SDPA 回退。普通 Frame Attention 不因此自动获得同一分支，须分别核对转置后 stride 与 contiguous 状态。
3. 无 residual 的 LayerNorm 改为先匹配权重 dtype，再调用 F.layer_norm；有 residual 的分支仍用 npu_add_layer_norm。该变更不是删除所有融合归一化。

## 验证与回退

分别检查标准/序列并行加载、Frame/Global Attention 与有无 residual 分支，对相同权重和输入比较输出与三任务精度，再测性能。README 的 A2/A3 环境表与代码新增 950 分支不是一份完整 950 软件矩阵；运行前仍须补齐目标环境验证。

初始化、布局或数值不通过时停止性能比较，恢复已验证的目标平台实现与配置；不能为消除报错把设备身份判断强制改成 A2。旧 [VGGT A2 卡](../../concepts/models/vggt.md) 的时延和量化数字不作为 950 验收基线。

## Evidence

PR133 已合入；固定 utils、demo、Attention 和 Block 代码具有上述分支。本批未在 950 执行 VGGT，也未补造性能数字。
