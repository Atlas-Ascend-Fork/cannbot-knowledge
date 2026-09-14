---
type: Concept
title: Sana-Video
description: Sana-Video 是 NVIDIA SANA 家族的视频生成模型，在 cann-recipes-infer 中作为轻量级多模态生成样例接入昇腾 NPU。相关优化集中在两类：**去噪网络的 conv 改写**（1×1 conv2d 转 matmul、时序 conv2d 的 HW 轴调换）与 **通用融合算子适配**（npu_rms_norm / npu_rotary_mul / npu_fusion_attention）。优化逻辑全部以 monkey patch 方式落在 `models/sana-video/patches/npu_patches.py`，通过 `inference_video_scripts/` 下的脚本调用。此外提供 **MX 块级量化推理**（`quant_type` a8w8=MXFP8 / a4w4=MXFP4，QuantLinear / Conv-as-Linear，`patches/quant_module.py`）。
tags:
- task.design
- topic.model_architecture
- topic.multimodal
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/sana-video/SANA-Video_optimization.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/patches/npu_patches.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/inference_video_scripts/inference_sana_video.py
  role: implementation
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-09-12T03:21:42Z'
platforms:
- a2
- a3
- '950'
---

# Sana-Video

## Summary

Sana-Video 是 NVIDIA SANA 家族的视频生成模型，在 cann-recipes-infer 中作为轻量级多模态生成样例接入昇腾 NPU。相关优化集中在两类：**去噪网络的 conv 改写**（1×1 conv2d 转 matmul、时序 conv2d 的 HW 轴调换）与 **通用融合算子适配**（npu_rms_norm / npu_rotary_mul / npu_fusion_attention）。优化逻辑全部以 monkey patch 方式落在 `models/sana-video/patches/npu_patches.py`，通过 `inference_video_scripts/` 下的脚本调用。此外提供 **MX 块级量化推理**（`quant_type` a8w8=MXFP8 / a4w4=MXFP4，QuantLinear / Conv-as-Linear，`patches/quant_module.py`）。

## Architecture And Serving Traits

- 属于 DiT 范式的视频生成模型（见 [dit](../modules/dit.md)）；此处的卷积和融合算子 patch 面向去噪网络。推理脚本单独用 `get_vae` 创建 VAE，用 `build_model` 创建去噪模型，并对后者的 `model.blocks[*].mlp` 同步时序卷积权重
- 主要文件：
 - `models/sana-video/patches/npu_patches.py` — 全部 NPU 适配 patch
 - `models/sana-video/inference_video_scripts/inference_sana_video.py` — 推理脚本，负责权重转换与 patch 应用
- 无文档级 figures；无 SP / CFG / 并行优化描述

### 统一推理拉起

部署经统一拉起架构 [mm-inference-launch](../frameworks/mm_inference_launch.md)：`models/sana-video/infer.sh` + YAML 场景切换，启动器为 `accelerate`（`launcher: accelerate`，`mixed_precision=bf16`、`DISABLE_XFORMERS=1`），`entry_script` 指向上述推理脚本。config 变体（`config/`，均单卡）：`2b_480p_single`（BF16 基线）、`2b_480p_single_a4w4`·`2b_480p_single_a8w8`（`model_args.quant_type` 切 a4w4 / a8w8 量化）、`2b_480p_single_platform`（平台模板，经 `infer_platform.sh` 生成临时本地权重配置）。

## Known Optimizations

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

推理入口将这些 patch 用于去噪网络，不能据此认定它们是 [VAE](../modules/vae.md) 优化。

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

### npu_rms_norm 算子适配（`patch_rms_norm`）

```python
def forward(self, x):
    if _npu_available:
        return torch_npu.npu_rms_norm(x, self.weight, epsilon=self.eps)[0]
    return original_forward(self, x)
```

[torch_npu.npu_rms_norm 文档](https://www.hiascend.com/document/detail/zh/Pytorch/710/apiref/torchnpuCustomsapi/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_rms_norm.md)

### npu_rotary_mul 算子适配（`patch_rotary_mul`）

```python
def apply_rotary_emb(hidden_states: torch.Tensor, freqs: torch.Tensor):
    if _npu_available:
        cos = freqs.real.unsqueeze(-1).expand(-1, -1, -1, -1, 2).flatten(-2)
        sin = freqs.imag.unsqueeze(-1).expand(-1, -1, -1, -1, 2).flatten(-2)
        x_out = torch_npu.npu_rotary_mul(hidden_states.permute(0, 1, 3, 2), cos, sin, "interleave")
        return x_out.permute(0, 1, 3, 2)
    else:
        x_rotated = torch.view_as_complex(hidden_states.permute(0, 1, 3, 2).to(torch.float64).unflatten(3, (-1, 2)))
        x_out = torch.view_as_real(x_rotated * freqs).flatten(3, 4).permute(0, 1, 3, 2)
        return x_out.type_as(hidden_states)

q_rotated = apply_rotary_emb(q, rotary_emb)
k_rotated = apply_rotary_emb(k, rotary_emb)
```

### npu_fusion_attention 算子适配（`patch_fusion_attention`）

```python
if mask is not None and mask.ndim == 2:
    mask = (1 - mask.to(q.dtype)) * -10000.0
    mask = mask[:, None, None].repeat(1, self.num_heads, num_tokens, 1)

if _npu_available:
    bool_mask = None if mask is None else mask < -1000
    x = torch_npu.npu_fusion_attention(
        q,
        k,
        v,
        q.shape[1],
        input_layout="BNSD",
        pse=None,
        atten_mask=bool_mask,
        scale=1.0 / math.sqrt(q.shape[-1]),
        pre_tockens=2147483647,
        next_tockens=2147483647,
        keep_prob=1,
    )[0]
else:
    x = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, dropout_p=0.0, is_causal=False)

x = x.transpose(1, 2).contiguous()
```

## MX 量化（a8w8 / a4w4）

`config/*.yaml` 的 `model_args.quant_type`（`bf16` / `a8w8` / `a4w4`，`patches/__init__.py` `VALID_QUANT_TYPES`）决定是否量化：非 `bf16` 时 `apply_all` 置 `enable_quant=True`，推理脚本在权重加载后对 DiT 各 block 调 `replace_quant_module(model, quant_mode=args.quant_type)`（`patches/quant_module.py`），用 MX 块级缩放（`quant_format="mxfp"`）把 DiT 的 Linear 与 1×1 Conv 替换为量化模块。a8w8 = MXFP8、a4w4 = MXFP4；MX 块级缩放的数值格式（E4M3 / E2M1、E8M0 block scale）见 [mxfp8-a8w8](../quantization/mxfp8_a8w8.md) / [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)。

### QuantLinear（MXFP8 / MXFP4）

DiT Linear 层（`block.attn.qkv/proj`、`block.cross_attn.q_linear/kv_linear/proj`）按 `quant_mode` 替换为 `QuantLinear`。激活与权重均经 `torch_npu.npu_dynamic_mx_quant` 动态 MX 量化后走 `torch_npu.npu_quant_matmul`（`group_sizes=[1, 1, 32]`，输出 `bfloat16`，`scale_dtype` / `pertoken_scale_dtype = torch_npu.float8_e8m0fnu`）。`forward_a8w8` 与 `forward_a4w4` 的主要差异在 `dst_type`（a4w4 另传 `x1_dtype`/`x2_dtype`，见下）；其中 `block.attn.proj` 固定走 `a8w8` 不随 `quant_mode` 变：

- **a8w8（MXFP8）**：`dst_type=torch.float8_e4m3fn`。
- **a4w4（MXFP4）**：`dst_type=torch_npu.float4_e2m1fn_x2`，`npu_quant_matmul` 额外传 `x1_dtype` / `x2_dtype = float4_e2m1fn_x2`。

### Conv 量化（承接 conv→matmul 改写）

上节 1×1 conv2d → matmul 的量化延伸是 `QuantConv1x1AsLinear`：把 1×1 `nn.Conv2d` 的权重 `view(out, in)` 后内部委托 `QuantLinear`，forward 在 NCHW↔(B, HW, C) 间转置走量化 linear。`replace_quant_module` 对 `block.mlp.inverted_conv.conv` / `block.mlp.point_conv.conv` 应用，固定 `"a8w8"`（不随 `quant_mode` 变 a4w4）。

`QuantConv2d`（`CONV2D_MODES={"a8w8"}`）则封装 `torch_npu.contrib.module.QuantConv2d`，`quant_format=torch_npu.hifloat8`：权重 `npu_dynamic_quant(quant_mode="pertoken")`、激活 `npu_dynamic_quant(quant_mode="pertensor")`，forward 内 `effective_scale = w_scale * x_scale`。注：`replace_quant_module` 当前对 MLP 卷积走的是 `QuantConv1x1AsLinear` 路径。

### a4w4 部分回退 a8w8

`replace_quant_module` 中 `block.attn.proj` 固定 `"a8w8"`、MLP 卷积固定 `QuantConv1x1AsLinear("a8w8")`；README 亦注明 a4w4 配置下部分层回退 a8w8。哪些层回退由上述代码与 README 文字给出，源未进一步展开回退的逐层精度理由（gap）。

### 性能

README「性能数据」分两表，量化对比表标注于 **Atlas 950**（Atlas A2/A3 表仅列 BF16：480p81f 单步 2.75 s / Diffusion sampling 132 s，无量化行）：

| 量化方式 | 规格 | 单步时延(s) | Diffusion sampling(s) | 整网耗时(s) |
| ---- | ---- | ---- | ---- | ---- |
| bf16 | 480p81f | 1.67 | 83.5 | 90.44 |
| 8bit (a8w8) | 480p81f | 1.46 | 73 | 79.38 |
| 4bit (a4w4) | 480p81f | 1.43 | 71.5 | 77.92 |

> 性能数值带平台前提（Atlas 950、单卡 480p 81f）；A2/A3 表无量化行（gap）。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/sana-video/SANA-Video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/sana-video/SANA-Video_optimization.md)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/npu_patches.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/sana-video/patches/npu_patches.py)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/quant_module.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/patches/quant_module.py)（`QuantLinear` / `QuantConv1x1AsLinear` / `QuantConv2d` / `replace_quant_module`、`LINEAR_MODES={a8w8,a4w4}`、`npu_dynamic_mx_quant` + `npu_quant_matmul`；MR!400 `ecbc110` Add SanaVideo 4bit/8bit quant）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/patches/__init__.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/patches/__init__.py)（`VALID_QUANT_TYPES={bf16,a8w8,a4w4}`、`apply_all` `enable_quant`）、[`models/sana-video/inference_video_scripts/inference_sana_video.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/inference_video_scripts/inference_sana_video.py)（L555-556 `replace_quant_module`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/sana-video/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/README.md)（`quant_type` bf16/a8w8/a4w4、Atlas 950 量化性能表、a4w4 部分回退 a8w8）、[`config/2b_480p_single_a8w8.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/config/2b_480p_single_a8w8.yaml) / [`config/2b_480p_single_a4w4.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/sana-video/config/2b_480p_single_a4w4.yaml)

## Links

- [dit](../modules/dit.md)
- [vae](../modules/vae.md)
- [mm-inference-launch](../frameworks/mm_inference_launch.md)
- [hunyuan-video](hunyuan_video.md)
- [hunyuan-image-3](hunyuan_image_3.md)
- [wan2.2-i2v](wan2_2_i2v.md)
- [mxfp8-a8w8](../quantization/mxfp8_a8w8.md)（a8w8 = MXFP8 块级缩放数值格式）
- [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)（a4w4 = MXFP4 `float4_e2m1fn_x2` 数值格式）

## Notes

- **gap**：优化说明未提供逐项消融或精度数据；模型 README 的整网性能数据见上表。shipped config 均单卡（`world_size: 1`），但 README 说明可将 `world_size` 调大切单机多卡 DP（`mm_function.sh` 自动转为 `accelerate --num_processes`），SP / CFG 等并行优化未涉及
- **gap**：`GLUMBConvTemp` 的语义与 SANA 原始结构关系在源中未展开
