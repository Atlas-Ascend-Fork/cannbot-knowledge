---
type: Concept
title: MXFP8 A8W8 (DiT Linear)
description: HunyuanVideo 针对 DiT 中 Linear 层（MLP / 投影层）的 Micro-scaling FP8 矩阵量化方案：权重按 group（默认 `group_size=32`）per-group 量化为 FP8 E4M3FN，激活按 token 维度 per-token 量化为同格式，scale 采用 E8M0（纯指数，1 字节）。实现 8-bit × 8-bit 矩阵乘（A8W8），权重显存减半、带宽需求 -50%。调用 `torch_npu.npu_dynamic_mx_quant` + `torch_npu.npu_quant_matmul` 完成量化与量化 GEMM。
tags:
- task.design
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/hunyuan-video/hunyuan_video_optimization.md
  role: primary
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- '950'
---

# MXFP8 A8W8 (DiT Linear)

## Summary

HunyuanVideo 针对 DiT 中 Linear 层（MLP / 投影层）的 Micro-scaling FP8 矩阵量化方案：权重按 group（默认 `group_size=32`）per-group 量化为 FP8 E4M3FN，激活按 token 维度 per-token 量化为同格式，scale 采用 E8M0（纯指数，1 字节）。实现 8-bit × 8-bit 矩阵乘（A8W8），权重显存减半、带宽需求 -50%。调用 `torch_npu.npu_dynamic_mx_quant` + `torch_npu.npu_quant_matmul` 完成量化与量化 GEMM。

## Mechanism

### 量化策略

- **Per-token（激活）**：每 token 独立 scale，适配 DiT 每步不同 token 分布
- **Per-group（权重，group_size=32）**：静态权重一次性量化，group 粒度平衡精度与压缩
- **E8M0 scale**：1 字节纯指数格式，显存占用极小

### 动态转换 Linear

```python
# 来源：hyvideo/modules/mxfp8_a8w8.py
def dynamic_convert_mxfp8_linear(module, original_dtype, params_to_keep=None):
 for key, layer in module.named_modules():
 # 仅转换 transformer 块中的 Linear
 if isinstance(layer, nn.Linear) and ('double_blocks' in key or 'single_blocks' in key):
 # 跳过 modulation 层和 1D 权重
 if len(layer.weight.shape) == 1 or 'mod' in key:
 continue
 mxfp8_weight, mxfp8_scale = torch_npu.npu_dynamic_mx_quant(
 layer.weight.data,
 dst_type=torch.float8_e4m3fn,
 )
 layer.weight.data = mxfp8_weight
 setattr(layer, "weight_scale", mxfp8_scale)
 setattr(layer, "forward", lambda input, m=layer: mxfp8_linear_forward(m, original_dtype, input))
```

### 量化 Linear 前向

```python
# 来源：hyvideo/modules/mxfp8_a8w8.py
def mxfp8_linear_forward(layer, original_dtype, x):
 x_quant, x_scale = torch_npu.npu_dynamic_mx_quant(x, dst_type=torch.float8_e4m3fn)
 output = torch_npu.npu_quant_matmul(
 x_quant,
 layer.weight.T,
 pertoken_scale=x_scale,
 bias=layer.bias.to(torch.float32),
 scale=layer.weight_scale.permute(1, 0, 2),
 output_dtype=original_dtype,
 pertoken_scale_dtype=torch_npu.float8_e8m0fnu,
 scale_dtype=torch_npu.float8_e8m0fnu,
 group_sizes=[1, 1, 32],
 )
 return output
```

## 量化范围

| 层类型 | 是否量化 | 说明 |
| ------ | -------- | ---- |
| `double_blocks` 中的 Linear | ✓ | 双流注意力块投影层 |
| `single_blocks` 中的 Linear | ✓ | 单流注意力块投影层 |
| Modulation 层（adaLN） | ✗ | 保持原始精度，保证调制精度 |
| 1D 权重层 | ✗ | 不适合量化 |

## Accuracy Impact

- 源未给出 MXFP8 对最终视频 PSNR / 感知质量的量化评测（unverified）
- 结论性描述：保持推理精度；未披露对比数据

## Applicable Scenarios

- DiT 类模型（HunyuanVideo 首发使用）
- 大 MLP / 大投影层占比高，矩阵乘带宽敏感的场景

## Constraints

- 要求 NPU 支持 `npu_dynamic_mx_quant` / `npu_quant_matmul` + E8M0 scale
- 仅量化 Transformer block 中的 2D Linear；adaLN / modulation 与 1D 权重跳过
- 与 FP8 attention 互不依赖，可单独或叠加使用

## Known Results

见 [fp8-attention](fp8_attention.md) 的 benchmark 表：MXFP8 单独开启 e2e 1.05–1.06×；与 FP8 attention 叠加（ulysses8）e2e 1.38×。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/hunyuan-video/hunyuan_video_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/hunyuan-video/hunyuan_video_optimization.md) MXFP8 矩阵量化 (A8W8)
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/hunyuan-video/hyvideo/modules/mxfp8_a8w8.py)

## Links

- [fp8-attention](fp8_attention.md)
- [hunyuan-video](../models/hunyuan_video.md)
- [dit](../modules/dit.md)
- [hybrid-mxfp8-mxfp4](hybrid_mxfp8_mxfp4.md)（MXFP8 的另一用途：DeepSeek-V4 LLM 在 950PR/DT 用 MXFP8 替换原生 FP8 做部分 Matmul，与本页 HunyuanVideo DiT Linear A8W8 为不同模型场景）
- [sana-video](../models/sana_video.md)（同款 MXFP8 `npu_dynamic_mx_quant`+`npu_quant_matmul` 用于 SANA DiT 的 `quant_type=a8w8`，`QuantLinear` / `QuantConv1x1AsLinear`）
- [hif8](../../../training/concepts/quantization/hif8.md)（跨域·训练：HiF8/MXFP8 低精度训练量化）
- [mindspeed](../../../training/concepts/frameworks/mindspeed.md)（跨域·训练：MindSpeed 低精度框架(MXFP8 打通 TP-MC2)）
- [deepseek-v3-low-precision-pretrain](../../../training/guides/recipes/deepseek_v3_low_precision_pretrain.md)（跨域·训练：V3 MXFP8/HiF8 低精度预训练）

<!-- cannbot:related:start -->
## 相关

- [950(Ascend950) MXFP8 fused-MoE：进分组 matmul 前激活量化 scale 必须打包成 [M, N//2, 2] 并中心化收口](../../optimizations/experience/rules/950_mxfp8_moe_activation_scale_packed_layout.md)（`related`）：《950 MXFP8 MoE scale 布局》要求“进分组 matmul 前，把 scale 从二维 `［M, N］` reshape 成打包三维 `［M, N//2, 2］`（相邻两个 scale 打进最后一维）”；《MXFP8 A8W8》给出“调用 `torch_npu.npu_dynamic_mx_quant` + `torch_npu.npu_quant_matmul` 完成量化与量化 GEMM。”，前者补充后者同类 E8M0 动态量化产物进入 950 分组矩阵乘前的专用布局收口。
- [HunyuanVideo](../models/hunyuan_video.md)（`related`）：“MXFP8 矩阵量化 (A8W8) ｜ 降低显存带宽 ｜ DiT Linear 层 MXFP8，权重显存减半”；“HunyuanVideo 针对 DiT 中 Linear 层（MLP / 投影层）的 Micro-scaling FP8 矩阵量化方案”。前者是模型配置，后者给出权重/激活分组和算子调用边界。
- [在 NPU 上对含 1×1 卷积的 DiT 做 MXFP 低比特量化 — 卷积当线性算·加载期模块替换 + a4w4 混合精度部分回退 a8w8](../../optimizations/experience/rules/dit_mxfp_lowbit_quant_conv_as_linear.md)（`related`）：1×1 Conv 的低比特量化需在加载期替换为量化 Linear，并关闭原有运行时快路径。
- [复用共享融合算子/量化方法到不同结构模型时的静默规格失配（MoE 默认 SiLU 遇 GEGLU、钳位 SwiGLU 需专用算子、mxfp8 Linear 丢 dense 的 bias）](../../runbooks/runtime/shared_fused_op_default_spec_mismatch.md)（`related`）：将 `MxFp8LinearMethod` 复用到带 bias 的 dense Linear 时，需保留并应用 bias，避免静默丢参。
- [视频 DiT 量化降显存 / 带宽：per-block FP8 注意力（主要收益，Ulysses-only）+ MXFP8 matmul（跳过 adaLN）](../../guides/experience/interventions/video_dit_fp8_mxfp8_quantization.md)（`related`）：视频 DiT 可优先评估 FP8 Attention，再叠加 MXFP8 MatMul；量化普通 2D Linear 时跳过 adaLN、modulation 和 1D 权重。
<!-- cannbot:related:end -->
