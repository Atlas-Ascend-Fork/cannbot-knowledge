---
type: Optimization
title: DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠
description: DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠。在昇腾上优化
  DiT/扩散生成模型里的 conv / LayerNorm 密集段时，几处数学等价的代数改写能把算子换到 NPU 更亲和的路径（matmul 算力 / 末轴亲和布局
  / 省一趟逐元素）。它们是等价变换、不改语义，只在满足前提时成立。
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
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/patches/npu_patches.py
  role: supporting
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-21T10:17:52Z'
platforms:
- a2
---



# DiT/CNN 层在昇腾的算子级代数改写：1×1 conv→matmul、卷积换末轴、LayerNorm+adaLN 折叠

## 条件 → 优先尝试什么

在昇腾上优化 [DiT](../../concepts/modules/dit.md)/扩散生成模型里的 conv / LayerNorm 密集段时，几处**数学等价的代数改写**能把算子换到 NPU 更亲和的路径（matmul 算力 / 末轴亲和布局 / 省一趟逐元素）。它们是等价变换、不改语义，只在满足前提时成立。

## 一、1×1 conv 等价改写为 matmul

只有在 `kernel_size=(1,1)`、`stride=1`、`padding=0`、`groups=1` 且布局/权重/bias对应时，下面的逐位置 Matmul 才与原 Conv2d 等价；可将其作为候选实现测量比较——1×1 卷积数学上等价于对每个空间位置的通道向量做一次 `Co×Ci` 线性变换，性能还受转置/contiguous成本、形状与平台影响，不承诺始终更快。**非 1×1 卷积保持原生实现**。

## 二、卷积维换到末轴（连续维）

来源针对所列时序卷积把计算维换到末轴作为优化候选，不能推导任意卷积都更快。若某卷积维原本沿非末轴（如 `(B,C,T,H*W)` 上用 kernel `(t,1)` 沿 T 轴的时序卷积），把该维与末轴调换、改用 kernel `(1,t)` 沿末轴卷积可命中亲和布局。

- **关键约束**：等价所需的权重 permute **必须在加载模型权重后一次性完成**，绝不放进 forward 每步 `nn.Parameter(...)` 新建（维护者 review 定）——否则每步重建参数抵消收益且可能出错。

## 三、LayerNorm + adaLN 调制折叠

DiT block 内 γ/β 恒为初始 1/0 的 LayerNorm 若紧跟 adaLN 调制（scale/shift），可用代数等价把 **LN 与调制折进单次 `npu_layer_norm_eval`**，省掉一趟逐元素 LN + modulate。

- **成立前提**：仅当被融 LN 的 γ/β **确为固定 1/0** 时成立，**非所有 LN 可折**。

## 通用先验

- 在 NPU 上遇到 1×1 conv、非末轴卷积、γ/β 固定的 LN+调制，都先想「有没有等价代数改写到更亲和算子」。
- 所有需要 permute/重排权重的等价改写，把 permute 放**权重加载后一次性**，不放 forward 热路径。

## 风险 / 边界

- 1×1还需满足上述stride/padding/groups等条件；源示例仅检查kernel_size，不代表代码已经验证全部数学前提。其他改写也需保持权重、布局与γβ语义，前提不满足时保留原实现。
- 属算子级微优化，收益随模型 conv/LN 占比而定（本组无独立 before→after 数字）。

## 相关经验

- 上游 DiT/视频模型搬昇腾的 monkeypatch + 融合算子替换整体方法见 [upstream-dit-video-monkeypatch-npu-adaptation](../../guides/bringup/upstream_dit_video_monkeypatch_npu_adaptation.md)。
- DiT 接融合算子/autocast 的 dtype·混精·RoPE cos-sin 精度对齐见 [precision-dit-fusion-autocast-cossin-dtype](precision_dit_fusion_autocast_cossin_dtype.md)。

## Sana 固定实现的改写对照

以下为固定 Sana 实现的对照节选，外层 dropout、norm、activation 等仍按对应调用链执行；1×1 替换须满足本卡列出的等价前提，不能只依据源代码中的 kernel_size 判断。

### 1×1 conv2d → matmul（`patch_conv1x1_matmul`）

`patch_conv1x1_matmul` 对 `diffusion.model.nets.basic_modules.ConvLayer.forward` 加入 1×1 conv2d 的判断与转换逻辑。以下片段省略外层 dropout、norm 和 activation；矩阵乘法等价替换要求 `stride=1`、`padding=0`、`groups=1`，不能仅按 kernel_size 推广到任意卷积。具体性能收益应按输入、平台和实际算子实现测量。

```python
if self.conv.kernel_size == (1, 1):
    B, Ci, H, W = x.shape
    Co, *_ = self.conv.weight.shape
    x_trans = x.view(B, Ci, -1).permute(0, 2, 1).contiguous()
    kernel_trans = self.conv.weight.view(Co, Ci)
    x = x_trans @ kernel_trans.T
    if self.conv.bias is not None:
        x += self.conv.bias
    x = x.permute(0, 2, 1).contiguous().view(B, Co, H, W)
else:
    x = self.conv(x)
```

推理入口将这些 patch 用于去噪网络，不能据此认定它们是 [VAE](../../concepts/modules/vae.md) 优化。

### 时序 conv2d 的 HW 轴调换（`patch_temporal_conv_swap`）

`patch_temporal_conv_swap` 对 `GLUMBConvTemp` 增加 `t_conv_swap` 并在 forward 中调用：时间卷积核从第一轴换到第二轴，输入由 `[B, C, T, H*W]` 转为 `[B, C, H*W, T]`，输出再转回。这里交换的是卷积输入的两个空间轴，不是视频原始的 H 与 W。

```python
self.t_conv_swap = nn.Conv2d(
    out_feature,
    out_feature,
    kernel_size=(1, t_kernel_size),
    stride=1,
    padding=(0, t_padding),
    bias=False,
)

x_reshaped = x.view(batch_size, time_steps, channels, height * width).permute(0, 2, 1, 3)
x_out = x_reshaped + self.t_conv_swap(x_reshaped.transpose(-1, -2)).transpose(-1, -2)
```

并在 `inference_video_scripts/inference_sana_video.py` 中加载权重后同步交换后权重：

```python
for block in model.blocks:
    block.mlp.t_conv_swap.weight = nn.Parameter(block.mlp.t_conv.weight.permute(0, 1, 3, 2))
```

## Evidence

- `diff 事实`（@4b572b9）：1×1 conv2d 改 matmul；时序 conv 换末轴 + 权重 permute 一次性（维护者 review）。
- `diff 事实`（@2c45117）：DiT block γ/β=1/0 的 LN+adaLN 折进单次 `npu_layer_norm_eval`，仅 γβ 固定时成立。
- 溯源下探：[cann-recipes-infer-pr-322-feat-add-sana-video-sample](https://gitcode.com/cann/cann-recipes-infer/merge_requests/322)、[cann-recipes-infer-pr-49-feat-add-wan2-2-i2v-model](https://gitcode.com/cann/cann-recipes-infer/merge_requests/49)
