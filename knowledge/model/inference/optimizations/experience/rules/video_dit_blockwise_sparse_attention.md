---
type: Optimization
title: 视频 DiT 块稀疏 Attention 使能 — must-keep 首帧/文本 + TopK/SVG 选型（TopK 需离线 profiling）
description: 视频 DiT 块稀疏 Attention 使能 — must-keep 首帧/文本 + TopK/SVG 选型（TopK 需离线 profiling）。长序列视频 dit（本经验覆盖 hunyuan-video），稠密 Attention 开销随序列长度放大、想降本时：上 blockwise-sparse-attention 丢弃低注意力块。仓提供 --sparse-method TopK|SVG 两种块稀疏策略。使能前须先解决两件事——首帧/文本 must-keep（正确性）与 TopK/SVG 选型（工程量）。
tags:
- task.optimization
- topic.attention
- topic.diffusion
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/342
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/355
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 视频 DiT 块稀疏 Attention 使能 — must-keep 首帧/文本 + TopK/SVG 选型（TopK 需离线 profiling）

## 条件 → 优先尝试

长序列视频 [dit](../../../concepts/modules/dit.md)（本经验覆盖 [hunyuan-video](../../../concepts/models/hunyuan_video.md)），稠密 Attention 开销随序列长度放大、想降本时：上 [blockwise-sparse-attention](../../../concepts/modules/blockwise_sparse_attention.md) 丢弃低注意力块。仓提供 `--sparse-method TopK|SVG` 两种块稀疏策略。使能前须先解决两件事——**首帧/文本 must-keep**（正确性）与 **TopK/SVG 选型**（工程量）。

## 规则一：首帧（sink frame）与文本 token 必须 must-keep，不可进稀疏路径

序列由 `sink_frame_len`（首帧 token）+ 图像 token + `txt_token_len`（文本 token）拼成。**把 `sink_frame_len + txt_len` 覆盖的块标为 must-keep**（`must_keep_indices_q/k`），无条件并入 sabi、稀疏 predictor 对它们不做丢弃。原因：HunyuanVideo 依赖首帧保留，若把首帧一并稀疏会损生成质量——**通用块稀疏 predictor 不能直接套用**，须为每种 predictor（TopK / SVG）派生模型专属 adapter 注入 must-keep 逻辑（维护者确认「hyvideo 涉及首帧保留，需要自定义一个类」）。

可迁移的 must-keep 布局手段（对任何「部分 token 强制保全 + 其余稀疏」的注意力都适用）：TopK adapter 在调稀疏算子前 `move_sink_frame_to_end`（把首帧挪到序列尾）、算子后 `move_sink_frame_back` 复原，以配合 must-keep 块布局；序列尾的 padding 区间不走稀疏、单独走全量 [fused-infer-attention-score](../../../concepts/kernels/fused_infer_attention_score.md)（FIA），两段结果 `torch.cat` 拼接。即「挪到端部 + must-keep 块 + padding 走全量」的组合。

## 规则二：TopK 非即插即用（需离线 CAC profiling），SVG 即插即用

- **TopK：有强前置。** 稀疏 mask 依赖一份**逐 step/layer/head** 的稀疏度配置，该配置来自一次 **offline profiling**：对每个 head，在预设 **CAC（cumulative attention coverage，累计注意力覆盖率）** 目标下遍历稀疏度、取满足该覆盖率的最大稀疏度；profiling 前还须把各 step/layer 的 q、k 张量落盘作输入。缺这一步 TopK 无有效稀疏配置。选 TopK 要预留这段离线工程量。
- **SVG：即插即用。** 无离线 profiling，直接开。
- **为何差异**：TopK 要「按覆盖率保住关键块」就必须先量出每个 head 的注意力分布（离线 profiling），才能定各 head 能丢多少而不掉质量——精度可控但重前置；SVG 用固定/结构化稀疏模式免了这一步，代价是加速更低。
- **算子前置（两种策略共有）**：块稀疏走 ops-transformer 的 `blitz_sparse_attention` 及其 torch 接口 `torch_bsa`，需先编译；接口 import 以 `try/except ImportError` 守卫（未编译时 `torch_bsa=None`、不阻塞稠密路径加载，但也跑不了稀疏）。

## Outcome / 依据（仓自报基准）

`hunyuan_video_optimization.md` 新增块稀疏性能表（相对稠密 baseline；**未标注硬件/卡数/CANN 版本/序列长度**）：

| Method | Sparsity | DiT Time(s) | E2E Time(s) | DiT Speedup | E2E Speedup |
|--|--|--:|--:|--:|--:|
| Baseline | – | 3459.52 | 3577.19 | 1.00× | 1.00× |
| TopK | 76% | 1839.48 | 1963.52 | 1.88× | 1.82× |
| SVG | 80% | 2036.18 | 2167.55 | 1.70× | 1.65× |

**关键取舍**：SVG 名义稀疏度（80%）**高于** TopK（76%），但 DiT/E2E 加速反而**低于** TopK——**名义稀疏度更高 ≠ 加速更高**；换更高加速的代价就是 TopK 的离线 profiling 工程量。仅 2 个稀疏配置（<3 受控点），不外推「稀疏度越高越快」的单调/通用律。

## 反例 / 边界 / 风险

- must-keep 缺失（直接套通用 predictor）会稀疏掉首帧/文本、损生成质量——这是使能前的硬约束，非可选优化。
- benchmark 仓自报、无独立复测，配置口径缺失。
- 未编译 `torch_bsa` 时稀疏路径不可用（守卫只保稠密路径不崩）；关闭稀疏（`no_sparse`）时的 NoneType 崩溃另见该 PR 的守卫修复。

## Evidence

- **代码事实**（clone 核对 `module/blockwise_sparse/sparse_method.py`）：`HunyuanVideoTopKAdapter.get_must_keep_blocks_indices` / `move_sink_frame_to_end` / `move_sink_frame_back` / `attention`、`HunyuanVideoSVGAdapter.get_must_keep_blocks_indices` 落实首帧/文本 must-keep；`sparse_method.py` 把 `import torch_bsa` 改 try/except 守卫。
- **doc 披露**：`README.md` 的 `--sparse-method TopK|SVG`；`hunyuan_video_optimization.md` 的 offline-profiling（CAC、逐 step/layer/head、需先存 q/k）章节与块稀疏性能表。
- **维护者确认**：hyvideo 涉及首帧保留，通用块稀疏 predictor 不能直接套用，须为其派生自定义 adapter 类注入 must-keep 逻辑。
- **仓自报**：块稀疏性能表为仓自报、无独立复测。
- 溯源下探：
  - [cann-recipes-infer-pr-342-feat-hunyuanvideo-support-block-wise-sparse-attention](https://gitcode.com/cann/cann-recipes-infer/merge_requests/342)
  - [cann-recipes-infer-pr-355-issue-sparse-attention-bug-readme](https://gitcode.com/cann/cann-recipes-infer/merge_requests/355)