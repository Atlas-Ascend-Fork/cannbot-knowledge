---
type: Optimization
title: 在 NPU 上对含 1×1 卷积的 DiT 做 MXFP 低比特量化 — 卷积当线性算·加载期模块替换 + a4w4 混合精度部分回退 a8w8
description: 含1×1卷积的DiT量化需在加载期替换模块并关闭BF16快路径；低位宽保留逐层回退，收益与质量按目标任务验收。
tags:
- task.optimization
- topic.diffusion
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/400
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-22T10:39:39Z'
platforms:
- '950'
---
# 在 NPU 上对含 1×1 卷积的 DiT 做 MXFP 低比特量化 — 卷积当线性算·加载期模块替换 + a4w4 混合精度部分回退 a8w8

## 适用场景

单卡 [dit](../../concepts/modules/dit.md) 视频/图像生成，想用 MXFP 低比特量化（[MXFP8 a8w8](../../concepts/quantization/mxfp8_a8w8.md) / MXFP4 a4w4）压端到端时延。做这类量化前先接住两条与"普通 Linear 量化"不同的坑：**(1) DiT 里的 1×1 卷积怎么量化；(2) a4w4 能不能整网铺**。收益幅度取决于实际模型、形状和平台，不能从单组来源推广。MXFP 混合位宽量化的机制说明见 [hybrid-mxfp8-mxfp4](../../concepts/quantization/hybrid_mxfp8_mxfp4.md)，本页给运行时的两条落地判断与收益预期。

## 问题信号

- DiT 的 MLP / patch-embed 里有 `nn.Conv2d(kernel_size=1×1)`（数学上等价逐位置线性投影），需先满足stride=1、padding=0、groups=1等[等价改写前提](dit_cnn_operator_algebraic_rewrite_npu.md)，bf16参考实现将它改写成运行时 `x_trans @ kernel_trans.T` 的 matmul 快路径。量化开启后**不能沿用这套 forward**——它假设每次 forward 现取 `self.conv.weight` 的 bf16 原始张量，而量化权重须在初始化时一次性量化好。若不改，量化路径要么取不到原始权重、要么对已量化模块重复走 bf16 逻辑。
- 直接把整张 DiT 全量降到 a4w4，部分层会掉精度；且原生卷积量化算子路径当前只实现 a8w8、没有 a4w4。

## 做什么

### 1. conv1×1 量化 = 加载期模块替换（卷积当线性算），不复用运行时快路径

把卷积的量化**下沉到加载期的模块替换**：在模型加载时把 `nn.Conv2d(1×1)` 整体换成一个"卷积当线性算"的量化模块（权重按 `weight.view(out_channels, in_channels)` 摊平成线性权重、init 时一次性量化）；forward 把 NCHW 重排为 `(b, hw, c)` 序列走量化 Linear、再排回 NCHW。参考实现的量化模块 `QuantConv1x1AsLinear`：

```python
class QuantConv1x1AsLinear(nn.Module):
    def __init__(self, conv, mode="a8w8"):
        super().__init__()
        self.out_channels = conv.out_channels
        self.linear = QuantLinear(conv, mode)   # QuantLinear.__init__ 支持 nn.Conv2d 输入，init 内量化权重
    def forward(self, x):
        b, c, h, w = x.shape
        x_trans = x.view(b, c, -1).permute(0, 2, 1).contiguous()   # NCHW -> (b, hw, c)
        out = self.linear(x_trans)
        return out.permute(0, 2, 1).contiguous().view(b, self.out_channels, h, w)
```

**关键配套：量化时必须把 bf16 的"conv1×1→matmul"运行时快路径显式门控关掉**。参考实现给该快路径的判据从 `if kernel_size == (1,1):` 改为 `if kernel_size == (1,1) and not enable_quant:`；量化开时走 `else: x = self.conv(x)`（此时 `self.conv` 已被换成量化模块）。二者不能并存——不关掉会对已被替换的量化 conv 重复走 bf16 分支或取不到原始权重。

### 2. a4w4 是混合精度，预留"部分层回退 a8w8"的空间

对 DiT 做 a4w4（4bit）量化时**不要预设可整网 a4w4**。参考实现在 a4w4 档下仍把若干对 4bit 敏感/无算子支持的层钉在 a8w8：按 block 逐层指定精度，输出投影与 MLP 的 1×1 卷积保留 a8w8、注意力/交叉注意力的 qkv 与投影跟随档位走 a4w4：

```python
for block in model.blocks:
    block.mlp.inverted_conv.conv = QuantConv1x1AsLinear(block.mlp.inverted_conv.conv, "a8w8")  # 钉 a8w8
    block.mlp.point_conv.conv    = QuantConv1x1AsLinear(block.mlp.point_conv.conv, "a8w8")      # 钉 a8w8
    block.attn.qkv          = QuantLinear(block.attn.qkv, quant_mode)   # 跟随档位（a4w4 档时=a4w4）
    block.attn.proj         = QuantLinear(block.attn.proj, "a8w8")      # 钉 a8w8
    block.cross_attn.q_linear  = QuantLinear(block.cross_attn.q_linear,  quant_mode)  # 跟随档位
    block.cross_attn.proj      = QuantLinear(block.cross_attn.proj,      quant_mode)
    block.cross_attn.kv_linear = QuantLinear(block.cross_attn.kv_linear, quant_mode)
```

即 a4w4 档下钉住 a8w8 的层 = {自注意力输出投影 `attn.proj`、MLP 的两个 1×1 卷积}。**下一个对 DiT 族做 a4w4 量化的 agent，先怀疑输出投影 + 1×1 卷积这类层对 4bit 敏感、优先给它们留 a8w8 回退位**；具体哪些层敏感由各模型标定，源未披露"为何这几层钉 a8w8"，故不外推为"输出投影必须 a8w8"的通用精度律。

## 参考 MXFP 量化算子约定（迁移时对齐）

- 格式映射：`a8w8` → 激活/权重 `torch.float8_e4m3fn`（MXFP8）；`a4w4` → `torch_npu.float4_e2m1fn_x2`（MXFP4）；两档 scale 均 `float8_e8m0fnu`。
- 计算：`npu_quant_matmul(..., group_sizes=[1, 1, 32])`（MX block=32）；激活每次 forward 经 `npu_dynamic_mx_quant(x.bfloat16(), ...)` 动态量化。
- 权重布局按档不同：a8w8 在 `npu_dynamic_mx_quant` 后对权重与 scale 再 `transpose`；a4w4 先 `weight.transpose(-1,-2)` 再量化并传 `axis=0`。
- 算子支持面：`LINEAR_MODES = {"a8w8","a4w4"}`（两档都支持）；`CONV2D_MODES = {"a8w8"}`（原生 `QuantConv2d` / HiF8 路径仅 a8w8，故 conv1×1 走"当线性算"而非原生卷积量化）。

## Benchmark（收益预期，仓自报、无独立复测）

固定Sana-Video档位数据由[Sana-Video 950来源观测](../../optimizations/benchmark_observations/sana_video_950_source_benchmark.md)维护；只有同一来源配置的对照，不作为所有DiT的收益预期。源缺量化质量指标，选择位宽前先验收任务精度。

## 何时不适用 / 风险

- 收益按目标任务分别测量；采样、cache或并行是不同改动，不能为了获得固定收益承诺而强制叠加。
- 上述层级划分/开关名/重排细节是该参考实现（cann-recipes-infer 的 SANA-Video 建模文件）的具体形态；可迁移的是"conv1×1 加载期模块替换 + 关 bf16 快路径""a4w4 预留部分层回退 a8w8"两条策略，具体层由各模型敏感性决定。
- DiT 视频模型搬上 NPU 的注意力/SP 后端 bringup 另见 [cuda-native-dit-video-attention-sp-npu-adaptation](cuda_native_dit_video_attention_sp_npu_adaptation.md)。

## Evidence

- **diff 事实 + 维护者确认**（clone `@9c08a4ba17d2`）：`models/sana-video/patches/quant_module.py` 新增 `QuantConv1x1AsLinear` / `replace_quant_module`，`npu_patches.py` 的 `patch_conv1x1_matmul` 分支加 `and not enable_quant`、签名多出 `enable_quant` 形参；`replace_quant_module` 中 `attn.proj` 与两处 MLP conv 硬编码 `"a8w8"`、其余传 `quant_mode`；`LINEAR_MODES` / `CONV2D_MODES` 常量。维护者确认"量化时权重在初始化时量化、不复用当前 forward、替换为 QuantConv1x1AsLinear"。
- **仓自报**（clone `@9c08a4ba17d2`）：Atlas 950 三行性能表出自 `models/sana-video/README.md`，无独立复测、无 correctness/精度数据；"为何这几层钉 a8w8"源未披露。
- 溯源下探：[cann-recipes-infer-pr-400-feat-add-sanavideo-4bit-8bit-quant](https://gitcode.com/cann/cann-recipes-infer/merge_requests/400)
