---
type: Optimization
title: DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠
description: DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠。在昇腾上优化 DiT/扩散生成模型里的 conv / LayerNorm 密集段时，几处数学等价的代数改写能把算子换到 NPU 更亲和的路径（matmul 算力 / 末轴亲和布局 / 省一趟逐元素）。它们是等价变换、不改语义，只在满足前提时成立。
tags:
- task.optimization
- topic.diffusion
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/322
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/49
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a2
---

# DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠

## 条件 → 优先尝试什么

在昇腾上优化 [DiT](../../../concepts/modules/dit.md)/扩散生成模型里的 conv / LayerNorm 密集段时，几处**数学等价的代数改写**能把算子换到 NPU 更亲和的路径（matmul 算力 / 末轴亲和布局 / 省一趟逐元素）。它们是等价变换、不改语义，只在满足前提时成立。

## 一、1×1 conv 等价改写为 matmul

kernel_size 为 (1,1) 的 conv2d **等价改写为 matmul 比走原生卷积更高效**——1×1 卷积数学上等价于对每个空间位置的通道向量做一次 `Co×Ci` 线性变换，改写后命中 NPU 的 matmul 算力。**非 1×1 卷积保持原生实现**。

## 二、卷积维换到末轴（连续维）

卷积落在张量**末轴（连续维）**更亲和。若某卷积维原本沿非末轴（如 `(B,C,T,H*W)` 上用 kernel `(t,1)` 沿 T 轴的时序卷积），把该维与末轴调换、改用 kernel `(1,t)` 沿末轴卷积可命中亲和布局。

- **关键约束**：等价所需的权重 permute **必须在加载模型权重后一次性完成**，绝不放进 forward 每步 `nn.Parameter(...)` 新建（维护者 review 定）——否则每步重建参数抵消收益且可能出错。

## 三、LayerNorm + adaLN 调制折叠

DiT block 内 γ/β 恒为初始 1/0 的 LayerNorm 若紧跟 adaLN 调制（scale/shift），可用代数等价把 **LN 与调制折进单次 `npu_layer_norm_eval`**，省掉一趟逐元素 LN + modulate。

- **成立前提**：仅当被融 LN 的 γ/β **确为固定 1/0** 时成立，**非所有 LN 可折**。

## 通用先验

- 在 NPU 上遇到 1×1 conv、非末轴卷积、γ/β 固定的 LN+调制，都先想「有没有等价代数改写到更亲和算子」。
- 所有需要 permute/重排权重的等价改写，把 permute 放**权重加载后一次性**，不放 forward 热路径。

## 风险 / 边界

- 每处改写都有成立前提（1×1 / γβ 固定 / 末轴亲和）；前提不满足时保持原实现。
- 属算子级微优化，收益随模型 conv/LN 占比而定（本组无独立 before→after 数字）。

## 相关经验

- 上游 DiT/视频模型搬昇腾的 monkeypatch + 融合算子替换整体方法见 [upstream-dit-video-monkeypatch-npu-adaptation](../../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)。
- DiT 接融合算子/autocast 的 dtype·混精·RoPE cos-sin 精度对齐见 [precision-dit-fusion-autocast-cossin-dtype](precision_dit_fusion_autocast_cossin_dtype.md)。

## Evidence

- `diff 事实`（@4b572b9）：1×1 conv2d 改 matmul；时序 conv 换末轴 + 权重 permute 一次性（维护者 review）。
- `diff 事实`（@2c45117）：DiT block γ/β=1/0 的 LN+adaLN 折进单次 `npu_layer_norm_eval`，仅 γβ 固定时成立。
- 溯源下探：[cann-recipes-infer-pr-322-feat-add-sana-video-sample](https://gitcode.com/cann/cann-recipes-infer/merge_requests/322)、[cann-recipes-infer-pr-49-feat-add-wan2-2-i2v-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/49)

<!-- cannbot:related:start -->
## 相关

- [在 NPU 上对含 1×1 卷积的 DiT 做 MXFP 低比特量化 — 卷积当线性算·加载期模块替换 + a4w4 混合精度部分回退 a8w8](dit_mxfp_lowbit_quant_conv_as_linear.md)（`same_topic`）：kernel_size 为 (1,1) 的 conv2d **等价改写为 matmul 比走原生卷积更高效**；把卷积的量化**下沉到加载期的模块替换**：在模型加载时把 `nn.Conv2d(1×1)` 整体换成一个"卷积当线性算"的量化模块；基础规则给出 1×1 卷积到 matmul 的数学等价快路，MXFP 规则补充量化开启后必须在加载期替换模块并关闭 BF16 运行时快路。
<!-- cannbot:related:end -->
