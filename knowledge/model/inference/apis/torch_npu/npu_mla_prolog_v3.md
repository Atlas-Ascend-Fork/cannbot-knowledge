---
type: API
title: MLA Prolog v3 四路前处理（torch_npu.npu_mla_prolog_v3）
description: torch_npu.npu_mla_prolog_v3：推理场景下Multi-Head Latent Attention前处理的计算操作。 MLA 前处理有四条并行路径：Query 的非 RoPE
  分量、Query 的 RoPE 分量、压缩 KV cache 与 RoPE key cache。
tags:
- task.lookup
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mla_prolog_v3.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
created_at: '2026-11-10T03:38:58Z'
updated_at: '2026-11-10T11:59:36Z'
platforms:
- a3
aliases:
- torch_npu.npu_mla_prolog_v3
---

# MLA Prolog v3 四路前处理：torch_npu.npu_mla_prolog_v3

## 用途与语义

推理场景下Multi-Head Latent Attention前处理的计算操作。

## 输入、输出与行为

MLA 前处理有四条并行路径：Query 的非 RoPE 分量、Query 的 RoPE 分量、压缩 KV cache 与 RoPE key cache。它们分属 Query 和 KV 两侧，不能因接口名称相近而套用 v2 的五路输出清单。

## 文档签名

```text
torch_npu.npu_mla_prolog_v3(token_x, weight_dq, weight_uq_qr, weight_uk, weight_dkv_kr, rmsnorm_gamma_cq, rmsnorm_gamma_ckv, rope_sin, rope_cos, kv_cache, kr_cache, cache_index=None, dequant_scale_x=None, dequant_scale_w_dq=None, dequant_scale_w_uq_qr=None, dequant_scale_w_dkv_kr=None, quant_scale_ckv=None, quant_scale_ckr=None, smooth_scales_cq=None, actual_seq_len=None, k_nope_clip_alpha=None, rmsnorm_epsilon_cq=1e-05, rmsnorm_epsilon_ckv=1e-05, cache_mode='PA_BSND', query_norm_flag=False, weight_quant_mode=0, kv_cache_quant_mode=0, query_quant_mode=0, ckvkr_repo_mode=0, quant_scale_repo_mode=0, tile_size=128, qc_qr_scale=1.0, kc_scale=1.0) -> (Tensor, Tensor, Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

## 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：Beta。

## 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

## Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/%EF%BC%88beta%EF%BC%89torch_npu-npu_mla_prolog_v3.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）
