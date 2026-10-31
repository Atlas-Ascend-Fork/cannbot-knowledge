---
type: Guide
title: Sana-Video NPU 适配、量化与生成验收流程
description: 当前Sana补丁时序、必传quant_type、加载后量化替换、本地离线权重、DP和950混合位宽验收。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/quant_module.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py
  role: implementation
created_at: '2026-10-21T09:56:21Z'
updated_at: '2026-10-29T14:16:27Z'
platforms:
- a2
- a3
- '950'
---

# Sana-Video NPU 适配、量化与生成验收流程

## 目标、输入与产物

面向固定来源中的 Sana-Video 实现，输入包括平台、权重、实际配置和任务指标；产物为可追溯配置、正确性/性能记录及回退入口。模型结构由[模型 Concept](../../concepts/models/sana_video.md)维护。以下描述固定版本实践，不能当作当前所有软件版本的部署保证。

## 1. 分别准备 DiT、VAE 和文本权重

本例去噪网络patch不等于VAE优化。普通infer.sh读取离线权重配置并用accelerate；infer_platform.sh为另一平台模板入口，会生成临时配置并执行依赖/权重准备。不得因其同名模型就混用启动步骤，机制见 [多模态启动](../../concepts/frameworks/mm_inference_launch.md)。

## 2. 按规范规则核对patch

当前README基线环境为CANN8.5.0、PyTorch2.6.0/torch_npu 2.6.0.post5（发布v7.3.0）；950量化还需相应MX算子和硬件，不能把基线安装示例当成每组量化测量build。普通YAML使用本地DiT、WanVAE、Gemma文本编码器并开启离线变量，先准备完整本地目录。

当前入口在上游导入前先调用patch_triton_rms_norm_import和patch_local_text_encoder_path；解析配置后才apply_all(args.quant_type)，该函数现在必须传bf16/a8w8/a4w4，旧无参调用失效。加载真实权重、同步t_conv_swap之后，量化档才replace_quant_module。普通入口accelerate，平台模板直python；多卡DP按prompt分发，不能当SP。


1×1 Conv转Matmul必须满足stride1、padding0、groups1等等价条件；时序Conv交换的是[T,H*W]两轴，加载后还要同步置换权重，不是交换视频原始H/W。机制由 [Conv改写规则](../../optimizations/rules/dit_cnn_operator_algebraic_rewrite_npu.md)维护。RMSNorm、interleave RoPE和非因果fusion_attention分别验收mask、layout、dtype与输出恢复，不能从单个融合算子推导整网精度。

## 3. 区分量化档和实际替换层

quant_type=bf16/a8w8/a4w4；当前量化模块用MXFP8/MXFP4的QuantLinear与Conv-as-Linear。a4w4配置仍把attn.proj、MLP的1×1卷积固定在a8w8，不写“全模型MXFP4”或用OR Scope表达混合组成。QuantConv2d类存在不表示replace_quant_module实际选择它；当前MLP使用QuantConv1x1AsLinear，按 [低比特Conv规则](../../optimizations/rules/dit_mxfp_lowbit_quant_conv_as_linear.md)核对。

## 4. 按平台选择数据并验收生成

当前README直接以Atlas 950标注，来源950档的量化对比集中 [950来源观测](../../optimizations/benchmark_observations/sana_video_950_source_benchmark.md)；A2/A3合并标注的一行数据没有区分具体硬件或实际测量精度（默认配置 BF16 不能证明测量使用 BF16），保留 [平台待细分草稿](../../optimizations/benchmark_observations/sana_video_bf16_source_observations.md)。不能把950量化结果外推给A2/A3。保存prompt、seed、步数与视频；比对质量与速度，源无逐项消融或精度记录，不默认选更低位宽。

## 验证、停止与回退

保存实际权重、软件版本、平台、并行组、输入与输出；以未启用待验优化的路径作对应基线，逐项比较 logits/任务质量、时延和峰值内存，并分别记录冷启动、warmup 与稳态重复测量。遇到源中未覆盖的形状、后端或平台时停止套用。失败后恢复对应版本的配置、权重与编译缓存，再按关联 Runbook 排查；没有实际跑通的回退不写为已验证。

本卡未记录独立的模型执行或硬件复测。来源自报和输出“看起来正常”不能替代本部署的精度验收；执行后应另存实际环境、配置和测量记录。

## 融合适配的输入输出对照

以下片段来自当前 Sana patch，供步骤 2 对照 dtype、layout、mask 和输出恢复；它们不是完整启动程序。Conv 改写与权重置换示例统一见上文规则入口。

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

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/README.md)（primary）
- [npu_patches.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/npu_patches.py)（implementation）
- [__init__.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/__init__.py)（implementation）
- [quant_module.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/patches/quant_module.py)（implementation）
- [inference_sana_video.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/sana-video/inference_video_scripts/inference_sana_video.py)（implementation）
