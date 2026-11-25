---
type: Optimization
title: "X114: 多分支汇聚单网格 + 单核头下沉"
description: "多分支卷积/多 kernel-size 算子按分支各 launch 一次会导致每次只占少量 cube 核；把分支折进同一张 block 表，并把小头阶段下沉到末阶段，可把多次低占用 launch 合成一次满核 launch。"
tags:
  - task.optimization
  - topic.compute.neighborhood.convolution
  - topic.attention
  - topic.data_movement.data_copy
  - topic.memory
  - topic.compute.reduction
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/tiling_strategy/inter_core_load_balance.md
    role: supporting
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/guide/operator_practice/simd_operator_optimization/overhead_optimization/core_count_kernel_type.md
    role: supporting
  - resource: https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x114.json
    role: evidence
  - resource: https://gitcode.com/cann/asc-devkit/blob/639b2b5c1031188107d23d785d52b935f1b4f13b/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreNumAic.md
    role: supporting
created_at: "2026-10-27T00:00:00Z"
updated_at: "2026-10-27T00:00:00Z"
platforms:
  - a2
---

> 迁移自 cannbot-skills `plugins-community/ops-perf-evolution/skills/evolution-knowledge/references/okf/`（原 OKF v1 卡，编号 X114）。
>
> 原始元数据：
>
> ```yaml
> id: X114
> origin: discovered
> confidence: single_op
> op_families: [convolution, cv-mix, matmul]
> bottlenecks: [tiling_imbalance, no_overlap, scalar_compute]
> ```

> 证据：基线/变体与逐 case 数据见 [证据包 cases/disc_x114.json](https://gitcode.com/liuyu15819/cannbot-skills/blob/f549d6d3320ac49e3e6e766600fd32bbaf37782a/cases/disc_x114.json)。
> 平台说明：`a2` 对应 Ascend 910B 系列（本卡实测型号见正文）；`a3` 对应 Ascend 910C 系列。

# Strategy X114: 多分支汇聚单网格 + 单核头下沉

## 核心思路
多分支（J 个 kernel size / 多专家）卷积类算子在基线里常写成 **per-branch kernel launch**：
每个分支各自 launch 一次 conv，分支内部 `totalBlk` 很小（小 shape 下 1-4 个 block），
于是每个 launch 只占 24 核里的 1-4 核，J 个 launch 串行。把分支折进 **同一张 block 表**
（`totalBlk = J*batch*mTiles*nTiles`，分支常量 kSize/pad/taps/权重偏移由 host 打包成
一个 int32 在 kernel 内解码）即可把 J 次低占用 launch 合成 1 次满核 launch。

配套的第二个杠杆：**单核串行的小头阶段**（如 SK Attention 的 fc→softmax→affine 链，BlockDim=1，
实测 32-112us）不要单独成 kernel，而是把 Z=fc(S) 按 (b, dd) 摊到多核，并把
w_j = Z·fcsW_j、softmax、attn·bnA/bnB **全部下沉进最后一阶段**（按 (b, 通道块) 并行），
中间量 attn/affA/affB 不再落 GM。

## 适用场景
- 多分支/多 kernel-size 卷积 + 汇聚（SK / ResNeXt / Inception / 多尺度检测头）；
- 症状：`op_summary` 里同一 op 名出现 J 次、每次 BlockDim 只有个位数，且存在 BlockDim=1 的小 kernel；
- 小/中 shape 段（延迟 bound）收益最大；大 shape（conv 吞吐 bound）收益主要来自少一次 launch 与头阶段。

## 实现要点
- block 表解码要保持与逐分支逐位一致的累加顺序（数值安全）；
- 分支常量打包用 int32 编码，避免新增 kernel 参数爆炸；
- 下沉头阶段后 attn/affA/affB 的 workspace 可整块删除（本例省 3 个 buffer 与对应 memset）；
- 输出直接按 `[B,C,H*W]` 精确长度写出，可同时消灭 `as_strided()+contiguous()` 布局拷贝。

## 来源

来自内部进化运行；运行标识、设备、用例与逐 case 数据见证据包。

## 问题现象
BlockDim 只有 1-4（24 AIC 大量空闲）；另有一个 BlockDim=1 的 fc→softmax→affine 头阶段

## 精度验证

精度判据与逐 case 结果见证据包；正文只保留机制与适用边界。

## 验证状态

本卡为 `status: stable`：定量结果与运行标识见证据包 `cases/disc_x114.json`；引用时请结合上文适用条件与失效边界判断适用范围。

